import { HoverCard } from "radix-ui";

/** One painted run of prompt text. Hover opens the card; click pins it in the right panel. */
export default function SegmentSpan({ segment, colour, pinned, onPin, card, children }) {
  return (
    <HoverCard.Root openDelay={150} closeDelay={80}>
      <HoverCard.Trigger asChild>
        <span
          data-verdict={colour ?? "unmeasured"}
          data-level={segment.level}
          data-pinned={pinned || undefined}
          onClick={(e) => {
            e.stopPropagation();
            onPin(segment.id);
          }}
          className="segment cursor-pointer"
        >
          {children}
        </span>
      </HoverCard.Trigger>
      <HoverCard.Portal>
        <HoverCard.Content
          side="right"
          align="start"
          sideOffset={8}
          collisionPadding={16}
          className="pop z-20 w-80 rounded-lg border border-line bg-panel p-4 shadow-pop"
        >
          {card}
        </HoverCard.Content>
      </HoverCard.Portal>
    </HoverCard.Root>
  );
}
