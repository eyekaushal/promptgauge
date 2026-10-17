/** The main column: one white panel with a hairline and radius 12 (DESIGN.md §6). */
export default function Panel({ children }) {
  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col rounded-lg border border-line bg-panel">
      {children}
    </div>
  );
}
