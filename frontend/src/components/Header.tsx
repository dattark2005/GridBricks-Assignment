import React from "react";
import { Database, Globe } from "lucide-react";

interface HeaderProps {
  dataSource: string;
  cacheStatus: string;
  periodStart: string;
  periodEnd: string;
}

export const Header: React.FC<HeaderProps> = ({
  dataSource,
  periodStart,
  periodEnd,
}) => {
  return (
    <header className="header-wrapper">
      <div className="title-group">
        <h1>
          <span>GridBricks</span>
          <span className="market-badge">UK Day-Ahead Wholesale Wind Evaluation</span>
        </h1>
        <p className="subtitle">
          Decision-support analytics assessing the accuracy of Day-Ahead wind generation forecasts
          (Elexon WINDFOR) available at the purchasing gate closure against outturn actual generation
          (Elexon FUELHH) for historical delivery periods in January 2026.
        </p>
      </div>

      <div className="header-status-box">
        <div className="status-pill">
          <Globe size={14} color="#38bdf8" />
          <span>Market TZ: <strong>Europe/London</strong></span>
        </div>
        <div className="status-pill">
          <Database size={14} color="#10b981" />
          <span>Source: <strong>{dataSource || "Elexon BMRS"}</strong></span>
        </div>
        <div className="status-pill">
          <div className="status-indicator-dot" />
          <span>Period: <strong>{periodStart} to {periodEnd}</strong></span>
        </div>
      </div>
    </header>
  );
};
