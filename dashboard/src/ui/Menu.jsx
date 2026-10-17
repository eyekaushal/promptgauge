import { DotsThree } from "@phosphor-icons/react";
import { DropdownMenu } from "radix-ui";

/**
 * The `…` menu of a run (DESIGN.md §7): items of icon + label. An item with `keepOpen` answers in
 * place (its label changes) instead of closing the menu. Everything here is read-only.
 * items: [{ label, Icon?, onSelect, keepOpen?, disabled? }]
 */
export default function Menu({ items, label = "more actions" }) {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          type="button"
          aria-label={label}
          className="flex size-8 items-center justify-center rounded-sm text-secondary hover:bg-surface-2 hover:text-ink data-[state=open]:bg-surface-3 data-[state=open]:text-ink"
        >
          <DotsThree size={18} weight="bold" />
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={6}
          collisionPadding={8}
          className="pop z-30 flex min-w-52 flex-col gap-0.5 rounded-md border border-line bg-panel p-1 shadow-pop"
        >
          {items.map(({ label: text, Icon = null, onSelect, keepOpen = false, disabled = false }) => (
            <DropdownMenu.Item
              key={text}
              disabled={disabled}
              onSelect={(event) => {
                if (keepOpen) event.preventDefault();
                onSelect();
              }}
              className="flex h-8 cursor-pointer items-center gap-2 rounded-sm px-2 text-base outline-none select-none data-[disabled]:cursor-not-allowed data-[disabled]:opacity-45 data-[highlighted]:bg-surface-2"
            >
              {Icon && <Icon size={14} className="text-secondary" aria-hidden="true" />}
              {text}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
