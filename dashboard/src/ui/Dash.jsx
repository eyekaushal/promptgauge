/** A null value: an en dash in tertiary, plus the word when the null has one (DESIGN.md §2). */
export default function Dash({ word = null }) {
  return (
    <span className="text-tertiary">
      {"–"}
      {word && <span className="ml-1">{word}</span>}
    </span>
  );
}
