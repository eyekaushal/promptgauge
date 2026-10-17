import { ArrowLeft, Flask } from "@phosphor-icons/react";
import { useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router";

import CodeBlock from "../ui/CodeBlock.jsx";
import Dash from "../ui/Dash.jsx";
import EmptyState from "../ui/EmptyState.jsx";
import { count, dateTime, delta, duration, score, usd } from "../ui/format.js";
import Panel from "../ui/Panel.jsx";
import SidePanel from "../ui/SidePanel.jsx";
import StatusTag from "../ui/StatusTag.jsx";
import Table from "../ui/Table.jsx";
import Tag from "../ui/Tag.jsx";
import TitleRow from "../ui/TitleRow.jsx";
import { useRequest } from "../ui/useRequest.js";

const RUN_COMMAND = "promptgauge eval --config promptgauge.yaml";

/** F8.2: the runs table (`/experiments`), one run's per-case table (`/experiments/:id`), and two
 * runs side by side (`/experiments?a=&b=`). */
export default function Experiments({ api }) {
  const { id } = useParams();
  const [params] = useSearchParams();
  const a = params.get("a");
  const b = params.get("b");
  if (id) return <ExperimentDetail api={api} id={Number(id)} />;
  if (a && b) return <Compare api={api} a={Number(a)} b={Number(b)} />;
  return <RunsTable api={api} />;
}

function RunsTable({ api }) {
  const navigate = useNavigate();
  const runs = useRequest(() => api.experiments(), [api]);
  const [picked, setPicked] = useState([]);
  const rows = runs.data ?? [];
  const scorerKeys = useMemo(() => unionKeys(rows.map((r) => r.scorer_means)), [rows]);

  const toggle = (id) =>
    setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id].slice(-2)));

  const columns = [
    {
      key: "pick",
      label: "",
      width: 32,
      render: (r) => (
        <input
          type="checkbox"
          aria-label={`pick ${r.name ?? r.id} to compare`}
          checked={picked.includes(r.id)}
          onChange={() => toggle(r.id)}
          onClick={(e) => e.stopPropagation()}
          className="accent-accent"
        />
      ),
    },
    { key: "name", label: "name", render: (r) => r.name ?? <Dash /> },
    { key: "kind", label: "kind", render: (r) => <Tag>{r.kind}</Tag> },
    { key: "model", label: "model" },
    ...scorerKeys.map((key) => ({
      key: `scorer:${key}`,
      label: key,
      align: "right",
      sortValue: (r) => r.scorer_means[key] ?? null,
      render: (r) => score(r.scorer_means[key]) ?? <Dash />,
    })),
    { key: "score", label: "score", align: "right", render: (r) => score(r.score) ?? <Dash /> },
    { key: "cases", label: "cases", align: "right", render: (r) => count(r.cases) },
    {
      key: "calls",
      label: "calls",
      align: "right",
      sortValue: (r) => r.totals.calls,
      render: (r) => (
        <span>
          {count(r.totals.calls)}
          <span className="text-tertiary"> · {count(r.totals.cached)} cached</span>
        </span>
      ),
    },
    {
      key: "cost",
      label: "cost",
      align: "right",
      sortValue: (r) => r.totals.cost_usd,
      render: (r) => usd(r.totals.cost_usd),
    },
    {
      key: "duration",
      label: "duration",
      align: "right",
      sortValue: (r) => Date.parse(r.finished_at ?? "") - Date.parse(r.created_at),
      render: (r) => duration(r.created_at, r.finished_at) ?? <Dash word="running" />,
    },
    { key: "created_at", label: "date", render: (r) => dateTime(r.created_at) },
    {
      key: "status",
      label: "status",
      render: (r) => <StatusTag status={r.status} stoppedReason={r.stopped_reason} />,
    },
  ];

  return (
    <Panel>
      <TitleRow title="Experiments" loading={runs.loading} error={runs.error}>
        {picked.length === 2 && (
          <button
            type="button"
            onClick={() => navigate(`/experiments?a=${picked[0]}&b=${picked[1]}`)}
            className="h-8 rounded-md bg-accent px-3 text-base text-accent-fg hover:opacity-90"
          >
            Compare
          </button>
        )}
        {picked.length === 1 && (
          <span className="text-sm text-secondary">pick one more run to compare</span>
        )}
      </TitleRow>
      {!runs.loading && rows.length === 0 ? (
        <EmptyState Icon={Flask} title="No runs yet" command={RUN_COMMAND} />
      ) : (
        <Table
          columns={columns}
          rows={rows}
          rowKey={(r) => r.id}
          onRowClick={(r) =>
            navigate(r.kind === "ablation" ? `/ablations/${r.id}` : `/experiments/${r.id}`)
          }
        />
      )}
    </Panel>
  );
}

function ExperimentDetail({ api, id }) {
  const navigate = useNavigate();
  const detail = useRequest(() => api.experiment(id), [api, id]);
  const results = useRequest(() => api.results(id), [api, id]);
  const hash = detail.data?.dataset_hash ?? null;
  const cases = useRequest(() => (hash ? api.cases(hash) : null), [api, hash]);
  const [showVariants, setShowVariants] = useState(false);
  const [selectedKey, setSelectedKey] = useState(null);

  const run = detail.data;
  const scorerKeys = run ? Object.keys(run.scorer_means) : [];
  const rows = useMemo(
    () => groupRuns(results.data ?? [], cases.data ?? [], scorerKeys, showVariants),
    [results.data, cases.data, scorerKeys, showVariants],
  );
  const selected = rows.find((r) => r.key === selectedKey) ?? null;
  const hasVariants = (results.data ?? []).some((r) => r.variant_id != null);

  const columns = [
    { key: "case_index", label: "#", align: "right", width: 48 },
    { key: "repeat_index", label: "repeat", align: "right", width: 64 },
    ...(showVariants
      ? [
          {
            key: "variant_id",
            label: "variant",
            align: "right",
            render: (r) => r.variant_id ?? <span className="text-tertiary">baseline</span>,
          },
        ]
      : []),
    { key: "input", label: "input" },
    { key: "output", label: "output", render: (r) => r.output ?? <Dash word="failed" /> },
    { key: "expected", label: "expected", render: (r) => r.expected ?? <Dash /> },
    ...scorerKeys.map((key) => ({
      key: `scorer:${key}`,
      label: key,
      align: "right",
      sortValue: (r) => r.scores[key]?.score ?? null,
      render: (r) => <ScoreCell result={r.scores[key]} />,
    })),
  ];

  return (
    <>
      <Panel>
        <TitleRow
          title={
            <span className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => navigate("/experiments")}
                aria-label="back to experiments"
                className="rounded-sm p-1 text-secondary hover:bg-surface-2"
              >
                <ArrowLeft size={16} />
              </button>
              {run?.name ?? `Experiment ${id}`}
            </span>
          }
          loading={detail.loading || results.loading || cases.loading}
          error={detail.error ?? results.error ?? cases.error}
        >
          {hasVariants && (
            <label className="flex items-center gap-2 text-sm text-secondary">
              <input
                type="checkbox"
                checked={showVariants}
                onChange={(e) => setShowVariants(e.target.checked)}
                className="accent-accent"
              />
              show variants
            </label>
          )}
        </TitleRow>
        {run && <RunHeader run={run} />}
        {run && rows.length === 0 && !results.loading ? (
          <EmptyState Icon={Flask} title="No results stored for this run" command={null} />
        ) : (
          <Table
            columns={columns}
            rows={rows}
            rowKey={(r) => r.key}
            onRowClick={(r) => setSelectedKey(r.key === selectedKey ? null : r.key)}
            selectedKey={selectedKey}
            rowClass={(r) => (r.failed ? "bg-danger-soft/40" : "")}
          />
        )}
      </Panel>
      {selected && (
        <SidePanel
          title={`Case ${selected.case_index} · repeat ${selected.repeat_index}`}
          subtitle={selected.variant_id == null ? "baseline" : `variant ${selected.variant_id}`}
          onClose={() => setSelectedKey(null)}
        >
          <CodeBlock label="input" text={selected.input} />
          <CodeBlock
            label={selected.output == null ? "output · failed" : "output"}
            text={selected.output}
            tone={selected.output == null ? "danger" : null}
          />
          <CodeBlock label="expected" text={selected.expected} />
          {scorerKeys.map((key) => {
            const result = selected.scores[key];
            return (
              <div key={key}>
                <div className="mb-1 flex items-center gap-2 text-xs font-medium text-secondary">
                  <span>{key}</span>
                  <ScoreCell result={result} />
                </div>
                {result?.reason != null && (
                  <CodeBlock label="judge reason" text={result.reason} />
                )}
              </div>
            );
          })}
        </SidePanel>
      )}
    </>
  );
}

function RunHeader({ run }) {
  const items = [
    ["status", <StatusTag key="s" status={run.status} stoppedReason={run.stopped_reason} />],
    ["kind", <Tag key="k">{run.kind}</Tag>],
    ["model", run.model],
    ["judge", run.judge],
    ["score", score(run.score) ?? <Dash />],
    ...Object.entries(run.scorer_means).map(([k, v]) => [k, score(v) ?? <Dash />]),
    ["cases", count(run.cases)],
    ["repeats", count(run.repeats)],
    ["calls", `${count(run.totals.calls)} · ${count(run.totals.cached)} cached`],
    ["cost", usd(run.totals.cost_usd)],
    ["duration", duration(run.created_at, run.finished_at) ?? <Dash word="running" />],
    ["date", dateTime(run.created_at)],
  ];
  return (
    <div className="flex flex-wrap gap-x-6 gap-y-2 border-b border-line px-5 py-3 text-sm">
      {items.map(([label, value]) => (
        <div key={label} className="flex items-baseline gap-1.5">
          <span className="text-xs font-medium text-secondary">{label}</span>
          <span>{value}</span>
        </div>
      ))}
    </div>
  );
}

/** A score, or the word "failed" on danger soft when the scorer produced no value. */
function ScoreCell({ result }) {
  if (!result) return <Dash word="not run" />;
  if (result.score == null) return <Tag tone="danger">failed</Tag>;
  return <span title={result.reason ?? undefined}>{score(result.score)}</span>;
}

function Compare({ api, a, b }) {
  const navigate = useNavigate();
  const compare = useRequest(() => api.compare(a, b), [api, a, b]);
  const data = compare.data;
  const scorerRows = data ? Object.entries(data.scorers).map(([key, v]) => ({ key, ...v })) : [];
  const nameOf = (run) => run.name ?? `#${run.id}`;

  const scorerColumns = data
    ? [
        { key: "key", label: "scorer" },
        { key: "a", label: nameOf(data.a), align: "right", render: (r) => score(r.a) ?? <Dash /> },
        { key: "b", label: nameOf(data.b), align: "right", render: (r) => score(r.b) ?? <Dash /> },
        { key: "delta", label: "delta", align: "right", render: (r) => <Delta value={r.delta} /> },
      ]
    : [];
  const caseColumns = data
    ? [
        { key: "index", label: "#", align: "right", width: 48 },
        { key: "input", label: "input" },
        { key: "a", label: nameOf(data.a), align: "right", render: (r) => score(r.a) ?? <Dash /> },
        { key: "b", label: nameOf(data.b), align: "right", render: (r) => score(r.b) ?? <Dash /> },
        { key: "delta", label: "delta", align: "right", render: (r) => <Delta value={r.delta} /> },
      ]
    : [];

  return (
    <Panel>
      <TitleRow
        title={
          <span className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => navigate("/experiments")}
              aria-label="back to experiments"
              className="rounded-sm p-1 text-secondary hover:bg-surface-2"
            >
              <ArrowLeft size={16} />
            </button>
            {data ? `${nameOf(data.a)} vs ${nameOf(data.b)}` : "Compare"}
          </span>
        }
        loading={compare.loading}
        error={compare.error}
      >
        {data && (
          <span className="text-sm text-secondary">
            overall {score(data.a.score) ?? "–"} → {score(data.b.score) ?? "–"} (
            <Delta value={data.delta} />)
          </span>
        )}
      </TitleRow>
      {data && (
        <div className="flex min-h-0 flex-1 flex-col">
          <div className="px-5 pt-3 text-xs font-medium text-secondary">per scorer</div>
          <div className="max-h-56 shrink-0">
            <Table columns={scorerColumns} rows={scorerRows} rowKey={(r) => r.key} />
          </div>
          <div className="px-5 pt-4 text-xs font-medium text-secondary">per case</div>
          <Table columns={caseColumns} rows={data.cases} rowKey={(r) => r.index} />
        </div>
      )}
    </Panel>
  );
}

function Delta({ value }) {
  if (value == null) return <Dash />;
  const tone = value > 0 ? "text-ok" : value < 0 ? "text-danger" : "text-secondary";
  return <span className={tone}>{delta(value)}</span>;
}

function unionKeys(objects) {
  const keys = [];
  for (const object of objects) for (const key of Object.keys(object)) if (!keys.includes(key)) keys.push(key);
  return keys;
}

/** Result rows → one row per (case, repeat, variant) with a `scores` map and the case's expected. */
function groupRuns(results, cases, scorerKeys, showVariants) {
  const expectedOf = new Map(cases.map((c) => [c.index, c]));
  const grouped = new Map();
  for (const r of results) {
    if (!showVariants && r.variant_id != null) continue;
    const key = `${r.variant_id ?? "base"}:${r.case_index}:${r.repeat_index}`;
    if (!grouped.has(key)) {
      const theCase = expectedOf.get(r.case_index);
      grouped.set(key, {
        key,
        case_index: r.case_index,
        repeat_index: r.repeat_index,
        variant_id: r.variant_id,
        input: theCase?.input ?? "",
        expected: theCase?.expected ?? null,
        output: r.output,
        scores: {},
        failed: false,
      });
    }
    const row = grouped.get(key);
    row.scores[r.scorer] = { score: r.score, reason: r.reason };
    if (r.score == null) row.failed = true;
  }
  return [...grouped.values()].sort(
    (x, y) =>
      (x.variant_id ?? -1) - (y.variant_id ?? -1) ||
      x.case_index - y.case_index ||
      x.repeat_index - y.repeat_index,
  );
}
