import { CircleNotch } from "@phosphor-icons/react";

/** 52 px: page title, a spinner while loading, an error line, actions on the right. */
export default function TitleRow({ title, loading = false, error = null, children = null }) {
  return (
    <div className="flex flex-col border-b border-line px-5">
      <div className="flex h-[52px] items-center gap-3">
        <h1 className="text-xl font-medium">{title}</h1>
        {loading && (
          <CircleNotch size={16} className="animate-spin text-secondary" aria-label="loading" />
        )}
        <div className="ml-auto flex items-center gap-2">{children}</div>
      </div>
      {error && <div className="pb-3 text-sm text-danger">{error.message}</div>}
    </div>
  );
}
