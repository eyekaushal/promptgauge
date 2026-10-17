import { X } from "@phosphor-icons/react";
import { Dialog } from "radix-ui";

import { useMediaQuery } from "./useMediaQuery.js";

/** The 360 px right column. Under 1100 px the same content opens as a 480 px dialog instead. */
export default function SidePanel({ title, subtitle = null, onClose, children }) {
  const wide = useMediaQuery("(min-width: 1100px)");
  if (!wide) {
    return (
      <Dialog.Root open onOpenChange={(open) => !open && onClose()}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-30 bg-ink/20" />
          <Dialog.Content className="pop fixed top-1/2 left-1/2 z-40 flex max-h-[85vh] w-[480px] max-w-[calc(100vw-32px)] -translate-x-1/2 -translate-y-1/2 flex-col rounded-lg border border-line bg-panel shadow-pop">
            <Header title={title} subtitle={subtitle} onClose={onClose} dialog />
            <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-5">{children}</div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    );
  }
  return (
    <aside className="flex w-[360px] shrink-0 flex-col rounded-lg border border-line bg-panel">
      <Header title={title} subtitle={subtitle} onClose={onClose} />
      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-5">{children}</div>
    </aside>
  );
}

function Header({ title, subtitle, onClose, dialog = false }) {
  const Title = dialog ? Dialog.Title : "div";
  const Description = dialog ? Dialog.Description : "div";
  return (
    <div className="flex h-[52px] shrink-0 items-center gap-2 border-b border-line px-5">
      <div className="min-w-0">
        <Title className="truncate text-lg font-semibold">{title}</Title>
        {subtitle ? (
          <Description className="truncate text-sm text-secondary">{subtitle}</Description>
        ) : (
          dialog && <Dialog.Description className="sr-only">{title}</Dialog.Description>
        )}
      </div>
      <button
        type="button"
        onClick={onClose}
        aria-label="close"
        className="ml-auto rounded-sm p-1 text-secondary hover:bg-surface-2"
      >
        <X size={16} />
      </button>
    </div>
  );
}
