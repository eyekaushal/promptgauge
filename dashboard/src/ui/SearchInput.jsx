import { MagnifyingGlass } from "@phosphor-icons/react";

/** 32 px input with a leading icon; filters client-side (F8.1). */
export default function SearchInput({ value, onChange, placeholder = "Search" }) {
  return (
    <label className="flex h-8 w-64 items-center gap-2 rounded-sm border border-line-strong bg-panel px-2 text-base focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-accent">
      <MagnifyingGlass size={14} className="text-secondary" />
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-tertiary"
      />
    </label>
  );
}
