import { Slider as Radix } from "radix-ui";

/** The delta control: 0.00 to 0.20, step 0.01, value shown beside it. Repaints client-side. */
export default function Slider({ value, onChange }) {
  return (
    <label className="flex items-center gap-3 text-sm">
      <span className="text-secondary">delta</span>
      <Radix.Root
        value={[value]}
        min={0}
        max={0.2}
        step={0.01}
        onValueChange={([v]) => onChange(v)}
        aria-label="delta"
        className="relative flex h-5 w-40 touch-none items-center select-none"
      >
        <Radix.Track className="relative h-0.5 flex-1 rounded-full bg-line-strong">
          <Radix.Range className="absolute h-full rounded-full bg-accent" />
        </Radix.Track>
        <Radix.Thumb className="block size-3.5 rounded-full border-2 border-accent bg-panel shadow-pop" />
      </Radix.Root>
      <span className="w-9 font-medium">{value.toFixed(2)}</span>
    </label>
  );
}
