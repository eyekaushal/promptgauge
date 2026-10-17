import { useMemo } from "react";

import SegmentCard from "./SegmentCard.jsx";
import SegmentSpan from "./SegmentSpan.jsx";
import { colourAt } from "./verdictRule.js";

/**
 * The prompt in monospace with every segment painted by its verdict at `delta`. Lines sit inside
 * their block and their own colour wins; text outside any segment stays plain.
 */
export default function PaintedPrompt({ text, segments, delta, legend, baseline, pinnedId, onPin }) {
  const { blocks, linesOf, blockNumber } = useMemo(() => arrange(segments), [segments]);
  const card = (segment) => (
    <SegmentCard
      segment={segment}
      colour={colourAt(segment, delta)}
      legend={legend}
      baseline={baseline}
      blockIndexOf={blockNumber}
    />
  );
  const span = (segment, key, children) => (
    <SegmentSpan
      key={key}
      segment={segment}
      colour={colourAt(segment, delta)}
      pinned={pinnedId === segment.id}
      onPin={onPin}
      card={card(segment)}
    >
      {children}
    </SegmentSpan>
  );

  const parts = [];
  let cursor = 0;
  for (const block of blocks) {
    if (block.start_offset > cursor) parts.push(text.slice(cursor, block.start_offset));
    const lines = linesOf.get(block.id) ?? [];
    if (lines.length === 0) {
      parts.push(span(block, block.id, text.slice(block.start_offset, block.end_offset)));
    } else {
      const inner = [];
      let at = block.start_offset;
      for (const line of lines) {
        if (line.start_offset > at) {
          inner.push(span(block, `${block.id}:${at}`, text.slice(at, line.start_offset)));
        }
        inner.push(span(line, line.id, text.slice(line.start_offset, line.end_offset)));
        at = line.end_offset;
      }
      if (block.end_offset > at) {
        inner.push(span(block, `${block.id}:${at}`, text.slice(at, block.end_offset)));
      }
      parts.push(
        <span key={block.id} data-verdict={colourAt(block, delta) ?? "unmeasured"} className="block-run">
          {inner}
        </span>,
      );
    }
    cursor = block.end_offset;
  }
  if (cursor < text.length) parts.push(text.slice(cursor));

  return (
    <pre className="painted font-mono text-mono whitespace-pre-wrap break-words" onClick={() => onPin(null)}>
      {parts}
    </pre>
  );
}

function arrange(segments) {
  const blocks = segments
    .filter((s) => s.level === "block")
    .sort((a, b) => a.start_offset - b.start_offset);
  const linesOf = new Map();
  for (const line of segments.filter((s) => s.level === "line")) {
    const list = linesOf.get(line.parent_segment_id) ?? [];
    list.push(line);
    linesOf.set(line.parent_segment_id, list);
  }
  for (const list of linesOf.values()) list.sort((a, b) => a.start_offset - b.start_offset);
  const number = new Map(blocks.map((b, i) => [b.id, i + 1]));
  return { blocks, linesOf, blockNumber: (id) => number.get(id) ?? "?" };
}
