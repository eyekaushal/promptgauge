import { HoverCard } from "radix-ui";
import { useRef, useState } from "react";

import Dash from "./Dash.jsx";
import { count, score } from "./format.js";
import Histogram from "./Histogram.jsx";

/**
 * A scorer mean in the runs table. Opening the hover card loads the run's detail once and shows
 * the per-case spread behind the mean (DESIGN.md §7).
 */
export default function ScoreSpread({ api, runId, scorerKey, mean }) {
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState(null);
  const loaded = useRef(false);
  if (mean == null) return <Dash />;

  const load = (open) => {
    if (!open || loaded.current) return;
    loaded.current = true;
    api
      .experiment(runId)
      .then(setDetail)
      .catch((e) => {
        loaded.current = false;
        setError(e);
      });
  };
  const values = detail ? detail.case_scores.map((c) => c.scorer_means[scorerKey]) : null;

  return (
    <HoverCard.Root openDelay={300} closeDelay={100} onOpenChange={load}>
      <HoverCard.Trigger asChild>
        <span className="cursor-default underline decoration-line-strong decoration-dotted underline-offset-2">
          {score(mean)}
        </span>
      </HoverCard.Trigger>
      <HoverCard.Portal>
        <HoverCard.Content
          side="top"
          sideOffset={6}
          collisionPadding={8}
          className="pop z-30 flex flex-col gap-2 rounded-md border border-line bg-panel px-3 py-2 text-sm shadow-pop"
        >
          <div className="flex items-baseline gap-2">
            <span className="text-md">{score(mean)}</span>
            <span className="text-secondary">{scorerKey}</span>
          </div>
          {error ? (
            <span className="text-danger">{error.message}</span>
          ) : values ? (
            <div className="flex items-center gap-3">
              <Histogram values={values} label={scorerKey} />
              <span className="text-secondary">
                {count(values.filter((v) => v != null).length)} cases
              </span>
            </div>
          ) : (
            <span className="text-secondary">loading</span>
          )}
        </HoverCard.Content>
      </HoverCard.Portal>
    </HoverCard.Root>
  );
}
