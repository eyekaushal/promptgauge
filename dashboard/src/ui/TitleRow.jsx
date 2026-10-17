import { CaretRight, CircleNotch } from "@phosphor-icons/react";
import { Link } from "react-router";

/**
 * 52 px: the screen's type icon, an optional breadcrumb parent (`crumb={{ label, to }}`), the
 * page title at xl 600, a spinner while loading, an error line, actions on the right.
 */
export default function TitleRow({
  title,
  Icon = null,
  crumb = null,
  loading = false,
  error = null,
  children = null,
}) {
  return (
    <div className="flex flex-col border-b border-line px-5">
      <div className="flex h-[52px] items-center gap-2">
        {Icon && <Icon size={18} weight="regular" className="shrink-0 text-secondary" />}
        {crumb && (
          <>
            <Link
              to={crumb.to}
              className="shrink-0 text-xl font-medium text-secondary hover:text-ink"
            >
              {crumb.label}
            </Link>
            <CaretRight size={14} className="shrink-0 text-tertiary" aria-hidden="true" />
          </>
        )}
        <h1 className="truncate text-xl font-semibold">{title}</h1>
        {loading && (
          <CircleNotch
            size={16}
            className="shrink-0 animate-spin text-secondary"
            aria-label="loading"
          />
        )}
        <div className="ml-auto flex shrink-0 items-center gap-2 pl-3">{children}</div>
      </div>
      {error && <div className="pb-3 text-sm text-danger">{error.message}</div>}
    </div>
  );
}
