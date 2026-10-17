import { GearSix } from "@phosphor-icons/react";

import EmptyState from "../ui/EmptyState.jsx";
import TitleRow from "../ui/TitleRow.jsx";

/** F8.4. Config echo, key status and display settings arrive at B17. */
export default function Settings() {
  return (
    <>
      <TitleRow title="Settings" />
      <EmptyState Icon={GearSix} title="Settings arrive at B17" command={null} />
    </>
  );
}
