/** Icon on a disc, a title, one line naming the CLI command to run (DESIGN.md §5). */
export default function EmptyState({ Icon, title, command }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 p-12 text-center">
      <span className="flex size-10 items-center justify-center rounded-full bg-surface-2">
        <Icon size={20} weight="regular" className="text-secondary" />
      </span>
      <div className="text-md">{title}</div>
      {command && (
        <code className="rounded-sm bg-surface-2 px-2 py-1 font-mono text-mono text-secondary">
          {command}
        </code>
      )}
    </div>
  );
}
