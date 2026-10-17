import { Flask } from "@phosphor-icons/react";

import EmptyState from "../ui/EmptyState.jsx";
import TitleRow from "../ui/TitleRow.jsx";

/** F8.2. Runs table, per-case table and compare arrive at B15. */
export default function Experiments() {
  return (
    <>
      <TitleRow title="Experiments" />
      <EmptyState
        Icon={Flask}
        title="No runs yet"
        command="promptgauge eval --config promptgauge.yaml"
      />
    </>
  );
}
