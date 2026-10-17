import { Scissors } from "@phosphor-icons/react";

import EmptyState from "../ui/EmptyState.jsx";
import Panel from "../ui/Panel.jsx";
import TitleRow from "../ui/TitleRow.jsx";

/** F8.3. Painted prompt, hover cards, slider and cut panel arrive at B16. */
export default function Ablation() {
  return (
    <Panel>
      <TitleRow title="Ablations" />
      <EmptyState
        Icon={Scissors}
        title="No ablations yet"
        command="promptgauge ablate --config promptgauge.yaml"
      />
    </Panel>
  );
}
