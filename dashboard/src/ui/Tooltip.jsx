import { Tooltip as Radix } from "radix-ui";

/** 300 ms delay, panel background, 11 px. Every coloured element carries one with its word. */
export default function Tooltip({ text, children, side = "top" }) {
  if (!text) return children;
  return (
    <Radix.Root delayDuration={300}>
      <Radix.Trigger asChild>{children}</Radix.Trigger>
      <Radix.Portal>
        <Radix.Content
          side={side}
          sideOffset={6}
          collisionPadding={8}
          className="pop z-30 max-w-72 rounded-sm border border-line bg-panel px-2 py-1 text-xs shadow-pop"
        >
          {text}
        </Radix.Content>
      </Radix.Portal>
    </Radix.Root>
  );
}

export const TooltipProvider = Radix.Provider;
