import { Database } from "@phosphor-icons/react";

import EmptyState from "../ui/EmptyState.jsx";
import TitleRow from "../ui/TitleRow.jsx";

/** F8.1. Table, side panel and search arrive at B15. */
export default function Datasets() {
  return (
    <>
      <TitleRow title="Datasets" />
      <EmptyState
        Icon={Database}
        title="No datasets yet"
        command="promptgauge eval --config promptgauge.yaml"
      />
    </>
  );
}
