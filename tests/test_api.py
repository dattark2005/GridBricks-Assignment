import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app
from backend.models import ElexonFuelHHItem, ElexonWindforItem

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "gridbricks-backend"


def test_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["timezone"] == "Europe/London"
    assert data["default_cutoff_time"] == "11:00"


@patch("backend.main.elexon_client.get_actual_generation")
@patch("backend.main.elexon_client.get_forecast_generation")
def test_evaluation_endpoint_success(mock_get_forecasts, mock_get_actuals):
    # Mock data
    delivery_time = "2026-01-02T12:00:00Z"
    mock_get_actuals.return_value = [
        ElexonFuelHHItem(
            dataset="FUELHH",
            startTime=delivery_time,
            settlementDate="2026-01-02",
            settlementPeriod=24,
            fuelType="WIND",
            generation=10000.0,
        )
    ]
    mock_get_forecasts.return_value = [
        ElexonWindforItem(
            dataset="WINDFOR",
            publishTime="2026-01-01T09:30:00Z",
            startTime=delivery_time,
            generation=9500.0,
        )
    ]

    response = client.get(
        "/api/evaluation?start_date=2026-01-02&end_date=2026-01-02&cutoff_time=11:00"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["period_start"] == "2026-01-02"
    assert data["period_end"] == "2026-01-02"
    assert data["decision_cutoff_time"] == "11:00"
    metrics = data["metrics"]
    assert metrics["matched_intervals_count"] == 1
    assert metrics["mae_mw"] == 500.0  # |9500 - 10000|
    assert metrics["mean_signed_error_mw"] == -500.0  # 9500 - 10000 = -500 (underforecast)


def test_evaluation_invalid_dates():
    # End date before start date
    response = client.get("/api/evaluation?start_date=2026-01-10&end_date=2026-01-05")
    assert response.status_code == 400
    assert "start_date must be before or equal to end_date" in response.json()["detail"]


def test_evaluation_invalid_cutoff():
    response = client.get("/api/evaluation?cutoff_time=25:00")
    assert response.status_code == 400
    assert "Invalid cutoff_time format" in response.json()["detail"]
