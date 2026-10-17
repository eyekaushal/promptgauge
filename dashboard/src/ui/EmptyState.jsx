import CodeBlock from "./CodeBlock.jsx";

/**
 * Icon on a disc, a title, one sentence saying why it is empty, the CLI command to run as a
 * CodeBlock with its copy button, and optional starter cards (DESIGN.md §5).
 * cards: [{ name, line }]
 */
export default function EmptyState({ Icon, title, sentence = null, command = null, cards = null }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 p-12 text-center">
      <span className="flex size-10 items-center justify-center rounded-full bg-surface-2">
        <Icon size={20} weight="regular" className="text-secondary" />
      </span>
      <div className="text-md">{title}</div>
      {sentence && <p className="max-w-md text-sm text-secondary">{sentence}</p>}
      {command && (
        <div className="w-full max-w-md text-left">
          <CodeBlock text={command} />
        </div>
      )}
      {cards && cards.length > 0 && (
        <div className="mt-2 grid w-full max-w-md grid-cols-2 gap-3 text-left">
          {cards.map((card) => (
            <div key={card.name} className="flex flex-col gap-1 rounded-lg border border-line p-3">
              <span className="font-mono text-mono font-medium">{card.name}</span>
              <span className="text-sm text-secondary">{card.line}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
