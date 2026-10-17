import { Database } from "@phosphor-icons/react";
import { useMemo, useState } from "react";

import CodeBlock from "../ui/CodeBlock.jsx";
import Dash from "../ui/Dash.jsx";
import EmptyState from "../ui/EmptyState.jsx";
import { count, dateTime, shortHash } from "../ui/format.js";
import Panel from "../ui/Panel.jsx";
import SearchInput from "../ui/SearchInput.jsx";
import SidePanel from "../ui/SidePanel.jsx";
import Table from "../ui/Table.jsx";
import Tag from "../ui/Tag.jsx";
import TitleRow from "../ui/TitleRow.jsx";
import { useRequest } from "../ui/useRequest.js";

/** F8.1: one table per dataset hash, row click opens the full text, search filters client-side. */
export default function Datasets({ api }) {
  const datasets = useRequest(() => api.datasets(), [api]);
  const [chosen, setChosen] = useState(null);
  const hash = chosen ?? datasets.data?.[0]?.dataset_hash ?? null;
  const cases = useRequest(() => (hash ? api.cases(hash) : null), [api, hash]);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState(null);

  const rows = useMemo(() => filterCases(cases.data ?? [], query), [cases.data, query]);
  const selected = (cases.data ?? []).find((c) => c.id === selectedId) ?? null;
  const current = (datasets.data ?? []).find((d) => d.dataset_hash === hash) ?? null;

  const columns = [
    { key: "index", label: "#", align: "right", width: 48 },
    { key: "input", label: "input" },
    {
      key: "expected",
      label: "expected",
      render: (c) => c.expected ?? <Dash />,
    },
    { key: "context", label: "context", render: (c) => c.context ?? <Dash /> },
    {
      key: "tags",
      label: "tags",
      sortValue: (c) => c.tags.join(" "),
      render: (c) => (
        <span className="flex gap-1">
          {c.tags.map((t) => (
            <Tag key={t}>{t}</Tag>
          ))}
        </span>
      ),
    },
  ];

  const empty = !datasets.loading && (datasets.data ?? []).length === 0;
  return (
    <>
      <Panel>
        <TitleRow
          title="Datasets"
          loading={datasets.loading || cases.loading}
          error={datasets.error ?? cases.error}
        >
          {(datasets.data ?? []).length > 0 && (
            <select
              value={hash ?? ""}
              onChange={(e) => {
                setChosen(e.target.value);
                setSelectedId(null);
              }}
              className="h-8 rounded-sm border border-line-strong bg-panel px-2 text-base"
              aria-label="dataset"
            >
              {datasets.data.map((d) => (
                <option key={d.dataset_hash} value={d.dataset_hash}>
                  {shortHash(d.dataset_hash)} · {count(d.case_count)} cases ·{" "}
                  {dateTime(d.first_seen)}
                </option>
              ))}
            </select>
          )}
          {hash && <SearchInput value={query} onChange={setQuery} placeholder="Search cases" />}
        </TitleRow>
        {empty ? (
          <EmptyState
            Icon={Database}
            title="No datasets yet"
            command="promptgauge eval --config promptgauge.yaml"
          />
        ) : (
          <>
            {current && (
              <div className="flex items-center gap-3 px-5 py-2 text-sm text-secondary">
                <span className="font-mono" title={current.dataset_hash}>
                  {current.dataset_hash}
                </span>
                <span>
                  {count(rows.length)} of {count(current.case_count)} cases
                </span>
              </div>
            )}
            <Table
              columns={columns}
              rows={rows}
              rowKey={(c) => c.id}
              onRowClick={(c) => setSelectedId(c.id === selectedId ? null : c.id)}
              selectedKey={selectedId}
            />
          </>
        )}
      </Panel>
      {selected && (
        <SidePanel
          title={`Case ${selected.index}`}
          subtitle={shortHash(selected.dataset_hash)}
          onClose={() => setSelectedId(null)}
        >
          <CodeBlock label="input" text={selected.input} />
          <CodeBlock label="expected" text={selected.expected} />
          <CodeBlock label="context" text={selected.context} />
          <div>
            <div className="mb-1 text-xs font-medium text-secondary">tags</div>
            {selected.tags.length ? (
              <div className="flex flex-wrap gap-1">
                {selected.tags.map((t) => (
                  <Tag key={t}>{t}</Tag>
                ))}
              </div>
            ) : (
              <Dash word="no tags" />
            )}
          </div>
        </SidePanel>
      )}
    </>
  );
}

function filterCases(cases, query) {
  const needle = query.trim().toLowerCase();
  if (!needle) return cases;
  return cases.filter((c) =>
    [c.input, c.expected, c.context, ...c.tags].some(
      (text) => text && text.toLowerCase().includes(needle),
    ),
  );
}
