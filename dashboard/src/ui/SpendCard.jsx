import { useLocation } from "react-router";

import { count, percent, usd } from "./format.js";
import Tooltip from "./Tooltip.jsx";
import { useRequest } from "./useRequest.js";

/**
 * The sidebar's bottom card (DESIGN.md §6): project name, total spend, runs and cached share with
 * one thin bar. Reads GET /api/summary again on every route change so a run started from the CLI
 * shows up without a reload. The database path is the tooltip.
 */
export default function SpendCard({ api, health }) {
  const { pathname } = useLocation();
  const summary = useRequest(() => api.summary(), [api, pathname]);
  const database = health.data?.database ?? null;
  const data = summary.data;
  const share = data && data.calls > 0 ? data.cached / data.calls : 0;
  const error = health.error ?? summary.error;

  return (
    <Tooltip text={database ? `database: ${database}` : null} side="right">
      <div className="flex flex-col gap-1.5 rounded-md bg-surface-2 px-3 py-2.5 text-sm">
        <div className="truncate text-xs font-medium text-ink">{projectName(database) || "Project"}</div>
        {error ? (
          <div className="text-secondary">{error.message}</div>
        ) : (
          <>
            <div className="flex items-baseline justify-between">
              <span className="text-secondary">Spend</span>
              <span className="text-md font-medium text-ink">{data ? usd(data.cost_usd) : "–"}</span>
            </div>
            <div className="text-secondary">
              {data ? `${count(data.runs)} ${data.runs === 1 ? "run" : "runs"} · ${percent(share)} cached` : "loading"}
            </div>
            <div className="h-1 w-full overflow-hidden rounded-full bg-surface-3" aria-hidden="true">
              <div
                className="h-full rounded-full bg-secondary transition-[width] duration-150 ease-out"
                style={{ width: `${Math.round(share * 100)}%` }}
              />
            </div>
          </>
        )}
      </div>
    </Tooltip>
  );
}

function projectName(database) {
  // The database lives at <project>/.promptgauge/promptgauge.db, so the project is two up.
  if (!database) return "";
  const parts = database.split("/").filter(Boolean);
  return parts.length >= 3 ? parts[parts.length - 3] : parts[0] ?? "";
}
