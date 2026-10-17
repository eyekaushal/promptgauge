import { Database, Flask, GearSix, Scissors } from "@phosphor-icons/react";
import { NavLink } from "react-router";

const ITEMS = [
  { to: "/datasets", label: "Datasets", Icon: Database },
  { to: "/experiments", label: "Experiments", Icon: Flask },
  { to: "/ablations", label: "Ablations", Icon: Scissors },
  { to: "/settings", label: "Settings", Icon: GearSix },
];

/** 200 px, fixed, never collapses: wordmark, four items, project and database at the bottom. */
export default function Sidebar({ health }) {
  const database = health.data?.database ?? null;
  return (
    <aside className="flex w-[200px] shrink-0 flex-col border-r border-line bg-canvas px-3 py-4">
      <Wordmark />
      <nav className="mt-6 flex flex-col gap-1">
        {ITEMS.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              "relative flex h-8 items-center gap-2 rounded-md px-2 text-base transition-colors " +
              "duration-120 ease-out hover:bg-surface-2 " +
              (isActive ? "bg-accent-soft text-ink" : "text-secondary")
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute top-1.5 bottom-1.5 left-0 w-0.5 rounded-full bg-accent" />
                )}
                <Icon size={16} weight="regular" />
                <span>{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto truncate text-sm text-tertiary" title={database ?? undefined}>
        {health.error ? (
          <span className="text-danger">{health.error.message}</span>
        ) : (
          <>
            <div className="truncate text-secondary">{projectName(database)}</div>
            <div className="truncate">{database ?? "connecting"}</div>
          </>
        )}
      </div>
    </aside>
  );
}

/** Three verdict discs then the word (DESIGN.md §0). */
function Wordmark() {
  return (
    <div className="flex items-center gap-2 px-2">
      <span className="flex gap-1">
        <span className="size-1.5 rounded-full bg-red" />
        <span className="size-1.5 rounded-full bg-grey" />
        <span className="size-1.5 rounded-full bg-green" />
      </span>
      <span className="font-mono text-base font-medium text-ink">promptgauge</span>
    </div>
  );
}

function projectName(database) {
  // The database lives at <project>/.promptgauge/promptgauge.db, so the project is two up.
  if (!database) return "";
  const parts = database.split("/").filter(Boolean);
  return parts.length >= 3 ? parts[parts.length - 3] : parts[0] ?? "";
}
