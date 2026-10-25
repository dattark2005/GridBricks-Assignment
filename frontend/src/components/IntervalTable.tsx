import React, { useState, useMemo } from "react";
import type { MatchedInterval } from "../types";
import { ArrowUpDown, ChevronLeft, ChevronRight, Eye, Search } from "lucide-react";

interface IntervalTableProps {
  intervals: MatchedInterval[];
  onSelectInterval: (interval: MatchedInterval) => void;
}

type SortField =
  | "start_time_utc"
  | "settlement_period"
  | "actual_generation_mw"
  | "forecast_generation_mw"
  | "signed_error_mw"
  | "abs_error_mw"
  | "abs_error_pct"
  | "lead_time_hours";

export const IntervalTable: React.FC<IntervalTableProps> = ({ intervals, onSelectInterval }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState<SortField>("abs_error_mw");
  const [sortAsc, setSortAsc] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [onlyHighErrors, setOnlyHighErrors] = useState(false);

  // Sorting and filtering logic
  const filteredData = useMemo(() => {
    return intervals.filter((iv) => {
      // Search term filter
      const matchesSearch =
        iv.start_time_utc.includes(searchTerm) ||
        iv.start_time_london.includes(searchTerm) ||
        iv.settlement_date.includes(searchTerm) ||
        (iv.settlement_period !== null && iv.settlement_period !== undefined && iv.settlement_period.toString().includes(searchTerm));

      // High error filter (> 2000 MW)
      const absErr = iv.abs_error_mw ?? 0;
      const matchesHighError = !onlyHighErrors || (iv.abs_error_mw !== null && iv.abs_error_mw !== undefined && absErr >= 2000);

      return matchesSearch && matchesHighError;
    });
  }, [intervals, searchTerm, onlyHighErrors]);

  const sortedData = useMemo(() => {
    return [...filteredData].sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      if (aVal === null || aVal === undefined) return sortAsc ? 1 : -1;
      if (bVal === null || bVal === undefined) return sortAsc ? -1 : 1;

      if (typeof aVal === "string") {
        return sortAsc
          ? (aVal as string).localeCompare(bVal as string)
          : (bVal as string).localeCompare(aVal as string);
      }

      return sortAsc ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number);
    });
  }, [filteredData, sortField, sortAsc]);

  // Pagination
  const totalPages = Math.ceil(sortedData.length / pageSize) || 1;
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false); // Default descending for errors
    }
  };

  return (
    <div className="table-card">
      <div className="table-header-bar">
        <div className="table-title-group">
          <h2>Interval-Level Forecast Error Analysis</h2>
          <span style={{ fontSize: 12, color: "#94a3b8" }}>
            Showing {sortedData.length} intervals. Click any row or &lsquo;Inspect&rsquo; to view historical forecast revisions.
          </span>
        </div>

        <div className="table-controls">
          <div style={{ position: "relative" }}>
            <Search size={14} style={{ position: "absolute", left: 10, top: 10, color: "#64748b" }} />
            <input
              type="text"
              placeholder="Search date or SP..."
              className="input-select"
              style={{ paddingLeft: 30, width: 170 }}
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>

          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#94a3b8", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={onlyHighErrors}
              onChange={(e) => {
                setOnlyHighErrors(e.target.checked);
                setCurrentPage(1);
              }}
            />
            Large Errors (&ge; 2,000 MW)
          </label>

          <select
            className="input-select"
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
          >
            <option value="25">25 rows</option>
            <option value="50">50 rows</option>
            <option value="100">100 rows</option>
          </select>
        </div>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th onClick={() => handleSort("start_time_utc")}>
                Delivery Time (UTC) <ArrowUpDown size={12} style={{ display: "inline" }} />
              </th>
              <th onClick={() => handleSort("settlement_period")}>
                SP <ArrowUpDown size={12} style={{ display: "inline" }} />
              </th>
              <th onClick={() => handleSort("actual_generation_mw")}>
                Actual (MW) <ArrowUpDown size={12} style={{ display: "inline" }} />
              </th>
              <th onClick={() => handleSort("forecast_generation_mw")}>
                Day-Ahead FC (MW) <ArrowUpDown size={12} style={{ display: "inline" }} />
              </th>
              <th onClick={() => handleSort("signed_error_mw")}>
                Signed Error <ArrowUpDown size={12} style={{ display: "inline" }} />
              </th>
              <th onClick={() => handleSort("abs_error_mw")}>
                Abs Error <ArrowUpDown size={12} style={{ display: "inline" }} />
              </th>
              <th onClick={() => handleSort("abs_error_pct")}>
                Error % <ArrowUpDown size={12} style={{ display: "inline" }} />
              </th>
              <th onClick={() => handleSort("lead_time_hours")}>
                Lead Time <ArrowUpDown size={12} style={{ display: "inline" }} />
              </th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((iv, idx) => {
              const signedErr = iv.signed_error_mw ?? 0;
              const isOver = iv.signed_error_mw !== null && iv.signed_error_mw !== undefined && signedErr > 0;
              const isUnder = iv.signed_error_mw !== null && iv.signed_error_mw !== undefined && signedErr < 0;
              const absErr = iv.abs_error_mw ?? 0;
              const isHigh = iv.abs_error_mw !== null && iv.abs_error_mw !== undefined && absErr >= 2000;

              return (
                <tr
                  key={iv.start_time_utc || idx}
                  style={{ background: isHigh ? "rgba(236, 72, 153, 0.05)" : undefined }}
                >
                  <td className="tabular">
                    <strong>{iv.start_time_utc.replace("T", " ").replace(":00Z", "")}</strong>
                  </td>
                  <td className="tabular">{iv.settlement_period || "—"}</td>
                  <td className="tabular" style={{ color: "#10b981", fontWeight: 600 }}>
                    {iv.actual_generation_mw !== null && iv.actual_generation_mw !== undefined
                      ? iv.actual_generation_mw.toLocaleString()
                      : "—"}
                  </td>
                  <td className="tabular" style={{ color: "#38bdf8", fontWeight: 600 }}>
                    {iv.forecast_generation_mw !== null && iv.forecast_generation_mw !== undefined
                      ? iv.forecast_generation_mw.toLocaleString()
                      : "—"}
                  </td>
                  <td
                    className="tabular"
                    style={{
                      fontWeight: 600,
                      color: isOver ? "#f59e0b" : isUnder ? "#ec4899" : "#94a3b8",
                    }}
                  >
                    {iv.signed_error_mw !== null && iv.signed_error_mw !== undefined
                      ? `${isOver ? "+" : ""}${iv.signed_error_mw.toLocaleString()}`
                      : "—"}
                  </td>
                  <td className="tabular">
                    {iv.abs_error_mw !== null && iv.abs_error_mw !== undefined
                      ? iv.abs_error_mw.toLocaleString()
                      : "—"}
                  </td>
                  <td className="tabular">
                    {iv.abs_error_pct !== null && iv.abs_error_pct !== undefined
                      ? `${iv.abs_error_pct.toFixed(1)}%`
                      : "—"}
                  </td>
                  <td className="tabular">
                    {iv.lead_time_hours !== null && iv.lead_time_hours !== undefined
                      ? `${iv.lead_time_hours}h`
                      : "—"}
                  </td>
                  <td>
                    <span
                      className={`badge-status ${
                        iv.status === "MATCHED" ? "badge-matched" : "badge-missing"
                      }`}
                    >
                      {iv.status}
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn-preset"
                      style={{ padding: "4px 8px", display: "inline-flex", alignItems: "center", gap: 4 }}
                      onClick={() => onSelectInterval(iv)}
                      title="Inspect all forecast revisions published for this delivery interval"
                    >
                      <Eye size={12} />
                      Vintages
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div
        style={{
          padding: "12px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderTop: "1px solid var(--border-color)",
          fontSize: 12,
          color: "#94a3b8",
        }}
      >
        <span>
          Page {currentPage} of {totalPages} ({filteredData.length} records)
        </span>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className="btn-preset"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          >
            <ChevronLeft size={14} /> Previous
          </button>
          <button
            className="btn-preset"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
          >
            Next <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
};
