import {
  ArrowDownRight,
  Database,
  Equals,
  Hash,
  Tag as TagIcon,
  TextAlignLeft,
} from "@phosphor-icons/react";
import { useMemo, useState } from "react";

import Chip from "../ui/Chip.jsx";
import CodeBlock from "../ui/CodeBlock.jsx";
import ColumnPicker from "../ui/ColumnPicker.jsx";
import Dash from "../ui/Dash.jsx";
import EmptyState from "../ui/EmptyState.jsx";
import { count, dateTime, shortHash } from "../ui/format.js";
import Panel from "../ui/Panel.jsx";
import SearchInput from "../ui/SearchInput.jsx";
import Section from "../ui/Section.jsx";
import SidePanel from "../ui/SidePanel.jsx";
import Table from "../ui/Table.jsx";
import Tag from "../ui/Tag.jsx";
import TitleRow from "../ui/TitleRow.jsx";
import { useColumns } from "../ui/useColumns.js";
import { useRequest } from "../ui/useRequest.js";

/** F8.1: one table per dataset hash, row click opens the full text, search filters client-side. */
export default function Datasets({ api }) {
  const datasets = useRequest(() => api.datasets(), [api]);
  const [chosen, setChosen] = useState(null);
  const hash = chosen ?? datasets.data?.[0]?.dataset_hash ?? null;
  const cases = useRequest(() => (hash ? api.cases(hash) : null), [api, hash]);
  const [query, setQuery] = useState("");
  const [tagFilters, setTagFilters] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const addTag = (tag) => setTagFilters((t) => (t.includes(tag) ? t : [...t, tag]));
  const removeTag = (tag) => setTagFilters((t) => t.filter((x) => x !== tag));

  const rows = useMemo(
    () => filterCases(cases.data ?? [], query, tagFilters),
    [cases.data, query, tagFilters],
  );
  const selected = (cases.data ?? []).find((c) => c.id === selectedId) ?? null;
  const current = (datasets.data ?? []).find((d) => d.dataset_hash === hash) ?? null;

  const columns = [
    { key: "index", label: "#", icon: Hash, align: "right", width: 48, fixed: true, muted: true },
    { key: "input", label: "input", icon: ArrowDownRight, fixed: true },
    {
      key: "expected",
      label: "expected",
      icon: Equals,
      render: (c) => c.expected ?? <Dash />,
    },
    { key: "context", label: "context", icon: TextAlignLeft, render: (c) => c.context ?? <Dash /> },
    {
      key: "tags",
      label: "tags",
      icon: TagIcon,
      sortValue: (c) => c.tags.join(" "),
      render: (c) => (
        <span className="flex gap-1">
          {c.tags.map((t) => (
            <Tag key={t} onClick={() => addTag(t)} tip={`filter by ${t}`}>
              {t}
            </Tag>
          ))}
        </span>
      ),
    },
  ];

  const shown = useColumns("datasets", columns);
  const empty = !datasets.loading && (datasets.data ?? []).length === 0;
  return (
    <>
      <Panel>
        <TitleRow
          title="Datasets"
          Icon={Database}
          loading={datasets.loading || cases.loading}
          error={datasets.error ?? cases.error}
          chips={
            current && (
              <Chip Icon={Database}>
                {count(rows.length)} of {count(current.case_count)} cases
              </Chip>
            )
          }
        >
          {(datasets.data ?? []).length > 0 && <ColumnPicker columns={shown} />}
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
          {tagFilters.map((t) => (
            <Tag key={t} onRemove={() => removeTag(t)} tip={`only cases tagged ${t}`}>
              {t}
            </Tag>
          ))}
          {hash && <SearchInput value={query} onChange={setQuery} placeholder="Search cases" />}
        </TitleRow>
        {empty ? (
          <EmptyState
            Icon={Database}
            title="No datasets yet"
            sentence="A dataset appears here the first time a run reads it; its cases are stored under the dataset's hash."
            command="promptgauge eval --config promptgauge.yaml"
          />
        ) : (
          <>
            {current && (
              <div className="flex items-center gap-3 px-5 py-2 text-sm text-secondary">
                <span className="font-mono" title="dataset hash: SHA-256 of the canonical cases">
                  {current.dataset_hash}
                </span>
              </div>
            )}
            {rows.length === 0 && (cases.data ?? []).length > 0 ? (
              <EmptyState
                Icon={Database}
                title="No rows match this filter"
                sentence="Clear the search or remove a tag chip to see the cases again."
              />
            ) : (
              <Table
                columns={shown.visible}
                rows={rows}
                rowKey={(c) => c.id}
                rowHeight={40}
                onRowClick={(c) => setSelectedId(c.id === selectedId ? null : c.id)}
                selectedKey={selectedId}
              />
            )}
          </>
        )}
      </Panel>
      {selected && (
        <SidePanel
          title={`Case ${selected.index}`}
          subtitle={shortHash(selected.dataset_hash)}
          onClose={() => setSelectedId(null)}
        >
          <Section Icon={ArrowDownRight} title="Input">
            <CodeBlock text={selected.input} />
          </Section>
          <Section Icon={Equals} title="Expected">
            <CodeBlock text={selected.expected} />
          </Section>
          <Section Icon={TextAlignLeft} title="Context">
            <CodeBlock text={selected.context} />
          </Section>
          <Section Icon={TagIcon} title="Tags">
            {selected.tags.length ? (
              <div className="flex flex-wrap gap-1">
                {selected.tags.map((t) => (
                  <Tag key={t} onClick={() => addTag(t)} tip={`filter by ${t}`}>
                    {t}
                  </Tag>
                ))}
              </div>
            ) : (
              <Dash word="no tags" />
            )}
          </Section>
        </SidePanel>
      )}
    </>
  );
}

/** The search text and every chosen tag must all match (filters compose). */
function filterCases(cases, query, tagFilters) {
  const needle = query.trim().toLowerCase();
  return cases.filter(
    (c) =>
      tagFilters.every((t) => c.tags.includes(t)) &&
      (!needle ||
        [c.input, c.expected, c.context, ...c.tags].some(
          (text) => text && text.toLowerCase().includes(needle),
        )),
  );
}
