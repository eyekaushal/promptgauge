import { Database, Flask, GearSix, Scissors } from "@phosphor-icons/react";
import { NavLink } from "react-router";

import SpendCard from "./SpendCard.jsx";

const ITEMS = [
  { to: "/datasets", label: "Datasets", Icon: Database },
  { to: "/experiments", label: "Experiments", Icon: Flask },
  { to: "/ablations", label: "Ablations", Icon: Scissors },
  { to: "/settings", label: "Settings", Icon: GearSix },
];

/** 220 px, fixed, never collapses: wordmark, a section label, four items, the spend card. */
export default function Sidebar({ api, health }) {
  return (
    <aside className="flex w-[220px] shrink-0 flex-col border-r border-line bg-canvas px-3 py-4">
      <Wordmark />
      <div className="mt-6 px-2 text-xs font-medium tracking-wide text-secondary uppercase">
        Project
      </div>
      <nav className="mt-1.5 flex flex-col gap-0.5">
        {ITEMS.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              "flex h-8 items-center gap-2 rounded-sm px-2 text-base transition-colors " +
              "duration-120 ease-out " +
              (isActive
                ? "bg-surface-3 font-medium text-ink"
                : "text-secondary hover:bg-surface-2 hover:text-ink")
            }
          >
            <Icon size={16} weight="regular" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto">
        <SpendCard api={api} health={health} />
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
