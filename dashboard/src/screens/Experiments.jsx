import {
  ArrowDownRight,
  ArrowUpRight,
  ArrowsLeftRight,
  Clock,
  Copy,
  Cpu,
  CurrencyDollar,
  DownloadSimple,
  Equals,
  Eye,
  EyeSlash,
  FileText,
  Flask,
  GitBranch,
  Hash,
  Lightning,
  Percent,
  Pulse,
  Repeat,
  Rows,
  Scissors,
  Stack,
  TextAa,
  Timer,
  Triangle,
} from "@phosphor-icons/react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router";

import Chip from "../ui/Chip.jsx";
import CodeBlock from "../ui/CodeBlock.jsx";
import ColumnPicker from "../ui/ColumnPicker.jsx";
import { downloadText, toCsv } from "../ui/csv.js";
import Dash from "../ui/Dash.jsx";
import EmptyState from "../ui/EmptyState.jsx";
import { count, dateTime, delta, duration, score, usd } from "../ui/format.js";
import Histogram from "../ui/Histogram.jsx";
import Menu from "../ui/Menu.jsx";
import MetricGrid from "../ui/MetricGrid.jsx";
import Panel from "../ui/Panel.jsx";
import Scatter from "../ui/Scatter.jsx";
import ScoreSpread from "../ui/ScoreSpread.jsx";
import Section from "../ui/Section.jsx";
import SegmentedControl from "../ui/SegmentedControl.jsx";
import SidePanel from "../ui/SidePanel.jsx";
import StatusTag from "../ui/StatusTag.jsx";
import Table from "../ui/Table.jsx";
import Tag from "../ui/Tag.jsx";
import TitleRow from "../ui/TitleRow.jsx";
import Tooltip from "../ui/Tooltip.jsx";
import { useColumns } from "../ui/useColumns.js";
import { useRequest } from "../ui/useRequest.js";
import { configToYaml } from "../ui/yaml.js";

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
  return <RunsTable api={api} preset={a ? Number(a) : null} />;
}

const FILTER_OPTIONS = [
  { value: "all", label: "all" },
  { value: "failed", label: "failed only", tip: "rows where a scorer produced no value" },
  { value: "low", label: "below 0.5", tip: "rows where any scorer scored under 0.5" },
];
const COMPARE_OPTIONS = (delta) => [
  { value: "all", label: "all" },
  { value: "different", label: "different only", tip: `rows whose delta is beyond ±${delta.toFixed(2)}, the run's delta` },
];

function RunsTable({ api, preset = null }) {
  const navigate = useNavigate();
  const runs = useRequest(() => api.experiments(), [api]);
  const [picked, setPicked] = useState(preset == null ? [] : [preset]);
  const rows = runs.data ?? [];
  const scorerKeys = useMemo(() => unionKeys(rows.map((r) => r.scorer_means)), [rows]);

  const toggle = (id) =>
    setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id].slice(-2)));

  const columns = [
    {
      key: "pick",
      label: "",
      width: 32,
      fixed: true,
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
    { key: "name", label: "name", icon: TextAa, fixed: true, render: (r) => r.name ?? <Dash /> },
    { key: "kind", label: "kind", icon: Stack, render: (r) => <Tag>{r.kind}</Tag> },
    { key: "model", label: "model", icon: Cpu },
    ...scorerKeys.map((key) => ({
      key: `scorer:${key}`,
      label: key,
      icon: Percent,
      align: "right",
      sortValue: (r) => r.scorer_means[key] ?? null,
      render: (r) => (
        <ScoreSpread api={api} runId={r.id} scorerKey={key} mean={r.scorer_means[key]} />
      ),
    })),
    {
      key: "score",
      label: "score",
      icon: Percent,
      align: "right",
      render: (r) => score(r.score) ?? <Dash />,
    },
    { key: "cases", label: "cases", icon: Rows, align: "right", render: (r) => count(r.cases) },
    {
      key: "calls",
      label: "calls",
      icon: Lightning,
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
      icon: CurrencyDollar,
      align: "right",
      sortValue: (r) => r.totals.cost_usd,
      render: (r) => usd(r.totals.cost_usd),
    },
    {
      key: "duration",
      label: "duration",
      icon: Timer,
      align: "right",
      sortValue: (r) => Date.parse(r.finished_at ?? "") - Date.parse(r.created_at),
      render: (r) => duration(r.created_at, r.finished_at) ?? <Dash word="running" />,
    },
    { key: "created_at", label: "date", icon: Clock, render: (r) => dateTime(r.created_at) },
    {
      key: "status",
      label: "status",
      icon: Pulse,
      render: (r) => <StatusTag status={r.status} stoppedReason={r.stopped_reason} />,
    },
  ];
  const shown = useColumns("runs", columns);

  return (
    <Panel>
      <TitleRow
        title="Experiments"
        Icon={Flask}
        loading={runs.loading}
        error={runs.error}
        chips={
          rows.length > 0 && (
            <Chip Icon={Flask}>
              {count(rows.length)} {rows.length === 1 ? "run" : "runs"}
            </Chip>
          )
        }
      >
        <ColumnPicker columns={shown} />
        {picked.length === 2 && (
          <button
            type="button"
            onClick={() => navigate(`/experiments?a=${picked[0]}&b=${picked[1]}`)}
            className="btn btn-primary"
          >
            <ArrowsLeftRight size={14} />
            Compare
          </button>
        )}
        {picked.length === 1 && (
          <span className="text-sm text-secondary">pick one more run to compare</span>
        )}
      </TitleRow>
      {!runs.loading && rows.length === 0 ? (
        <EmptyState
          Icon={Flask}
          title="No runs yet"
          sentence="Runs appear here as soon as the CLI has written one. Start with an eval, then ablate the same prompt."
          command={RUN_COMMAND}
          cards={[
            { name: "eval", line: "Scores the prompt against every case: the baseline an ablation is measured against." },
            { name: "ablate", line: "Removes each segment in turn and paints the prompt by the measured effect of its removal." },
          ]}
        />
      ) : (
        <Table
          columns={shown.visible}
          rows={rows}
          rowKey={(r) => r.id}
          numbered
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
  const [pretty, setPretty] = useState(true);
  const [filter, setFilter] = useState("all");
  const [configOpen, setConfigOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const run = detail.data;
  const scorerKeys = run ? Object.keys(run.scorer_means) : [];
  const allRows = useMemo(
    () => groupRuns(results.data ?? [], cases.data ?? [], scorerKeys, showVariants),
    [results.data, cases.data, scorerKeys, showVariants],
  );
  const rows = useMemo(() => allRows.filter((r) => matchesFilter(r, filter)), [allRows, filter]);
  const selected = allRows.find((r) => r.key === selectedKey) ?? null;

  const copyPrompt = () => {
    navigator.clipboard?.writeText(run?.prompt_text ?? "").then(() => setCopied(true));
  };
  useEffect(() => {
    if (!copied) return undefined;
    const timer = setTimeout(() => setCopied(false), 1200);
    return () => clearTimeout(timer);
  }, [copied]);
  const menuItems = run
    ? [
        { label: copied ? "Copied" : "Copy prompt", Icon: Copy, onSelect: copyPrompt, keepOpen: true },
        { label: "View config", Icon: FileText, onSelect: () => setConfigOpen(true) },
        {
          label: "Download results (CSV)",
          Icon: DownloadSimple,
          disabled: allRows.length === 0,
          onSelect: () => downloadText(`${run.name ?? `experiment-${id}`}-results.csv`, resultsCsv(allRows, scorerKeys)),
        },
        { label: "Compare with…", Icon: ArrowsLeftRight, onSelect: () => navigate(`/experiments?a=${id}`) },
        ...(run.kind === "ablation"
          ? [{ label: "Open ablation", Icon: Scissors, onSelect: () => navigate(`/ablations/${id}`) }]
          : []),
      ]
    : [];
  const hasVariants = (results.data ?? []).some((r) => r.variant_id != null);

  const columns = [
    { key: "case_index", label: "#", icon: Hash, align: "right", width: 48, fixed: true, muted: true },
    { key: "repeat_index", label: "repeat", icon: Repeat, align: "right", width: 72 },
    ...(showVariants
      ? [
          {
            key: "variant_id",
            label: "variant",
            icon: GitBranch,
            align: "right",
            render: (r) => r.variant_id ?? <span className="text-tertiary">baseline</span>,
          },
        ]
      : []),
    { key: "input", label: "input", icon: ArrowDownRight },
    {
      key: "output",
      label: "output",
      icon: ArrowUpRight,
      render: (r) => r.output ?? <Dash word="failed" />,
    },
    { key: "expected", label: "expected", icon: Equals, render: (r) => r.expected ?? <Dash /> },
    ...scorerKeys.map((key) => ({
      key: `scorer:${key}`,
      label: key,
      icon: Percent,
      align: "right",
      sortValue: (r) => r.scores[key]?.score ?? null,
      render: (r) => <ScoreCell result={r.scores[key]} />,
    })),
  ];
  const shown = useColumns("results", columns);

  return (
    <>
      <Panel>
        <TitleRow
          title={run?.name ?? `Experiment ${id}`}
          Icon={Flask}
          crumb={{ label: "Experiments", to: "/experiments" }}
          loading={detail.loading || results.loading || cases.loading}
          error={detail.error ?? results.error ?? cases.error}
          chips={run && <RunChips run={run} />}
        >
          <SegmentedControl options={FILTER_OPTIONS} value={filter} onChange={setFilter} label="display" />
          <ColumnPicker columns={shown} />
          {hasVariants && (
            <button
              type="button"
              aria-pressed={showVariants}
              onClick={() => setShowVariants((v) => !v)}
              className="btn btn-secondary"
            >
              {showVariants ? <EyeSlash size={14} /> : <Eye size={14} />}
              {showVariants ? "hide variants" : "show variants"}
            </button>
          )}
          {run && <Menu items={menuItems} label="run actions" />}
        </TitleRow>
        {run && <RunHeader run={run} configOpen={configOpen} onConfigOpen={setConfigOpen} />}
        {run && allRows.length === 0 && !results.loading ? (
          <EmptyState
            Icon={Flask}
            title="No results stored for this run"
            sentence="This run wrote no result rows; it may have stopped before its first case finished."
          />
        ) : run && rows.length === 0 && !results.loading ? (
          <EmptyState
            Icon={Flask}
            title="No rows match this filter"
            sentence={`${count(allRows.length)} rows are hidden by "${FILTER_OPTIONS.find((o) => o.value === filter)?.label}".`}
          />
        ) : (
          <Table
            columns={shown.visible}
            rows={rows}
            rowKey={(r) => r.key}
            rowHeight={40}
            onRowClick={(r) => setSelectedKey(r.key === selectedKey ? null : r.key)}
            selectedKey={selectedKey}
            rowClass={(r) => (r.failed ? "bg-danger-soft/40" : "")}
            rowTitle={(r) => (r.failed ? "a scorer failed on this run" : null)}
          />
        )}
      </Panel>
      {selected && (
        <SidePanel
          title={`Case ${selected.case_index} · repeat ${selected.repeat_index}`}
          subtitle={selected.variant_id == null ? "baseline" : `variant ${selected.variant_id}`}
          onClose={() => setSelectedKey(null)}
        >
          <Section Icon={ArrowDownRight} title="Input">
            <CodeBlock text={selected.input} />
          </Section>
          <Section
            Icon={ArrowUpRight}
            title={selected.output == null ? "Output · failed" : "Output"}
            actions={
              <SegmentedControl
                size="sm"
                label="output format"
                options={[
                  { value: "pretty", label: "Pretty", tip: "wrapped to the panel" },
                  { value: "raw", label: "Raw", tip: "as written; scrolls sideways" },
                ]}
                value={pretty ? "pretty" : "raw"}
                onChange={(v) => setPretty(v === "pretty")}
              />
            }
          >
            <CodeBlock
              text={selected.output}
              tone={selected.output == null ? "danger" : null}
              wrap={pretty}
            />
          </Section>
          <Section Icon={Equals} title="Expected">
            <CodeBlock text={selected.expected} />
          </Section>
          <Section Icon={Percent} title="Scores">
            {scorerKeys.map((key) => {
              const result = selected.scores[key];
              return (
                <div key={key} className="flex flex-col gap-1">
                  <div className="flex items-center justify-between gap-2 text-sm">
                    <span className="truncate">{key}</span>
                    <ScoreCell result={result} />
                  </div>
                  {result?.reason != null && (
                    <CodeBlock label="judge reason" text={result.reason} />
                  )}
                </div>
              );
            })}
          </Section>
        </SidePanel>
      )}
    </>
  );
}

/** The metric grid under the title (DESIGN.md §7) and a closed `config` section with the YAML. */
function RunHeader({ run, configOpen, onConfigOpen }) {
  const groups = [
    [
      {
        label: "status",
        value: <StatusTag status={run.status} stoppedReason={run.stopped_reason} />,
      },
      { label: "kind", value: <Tag>{run.kind}</Tag> },
    ],
    [
      { label: "model", value: run.model },
      { label: "judge", value: run.judge },
    ],
    [
      { label: "score", value: score(run.score) ?? <Dash /> },
      ...Object.entries(run.scorer_means).map(([k, v]) => ({
        key: `scorer:${k}`,
        label: k,
        value: (
          <span className="flex items-center gap-2">
            {score(v) ?? <Dash />}
            <Histogram values={run.case_scores.map((c) => c.scorer_means[k])} label={k} />
          </span>
        ),
      })),
    ],
    [
      { label: "repeats", value: count(run.repeats) },
      { label: "date", value: dateTime(run.created_at) },
    ],
  ];
  return (
    <>
      <MetricGrid groups={groups} />
      <div className="border-b border-line px-5 py-2">
        <Section Icon={FileText} title="config" open={configOpen} onOpenChange={onConfigOpen}>
          <CodeBlock text={configToYaml(run.config)} numbered yaml />
        </Section>
      </div>
    </>
  );
}

/** The run's totals as title-row chips: cases, calls (with cached), cost, duration. */
export function RunChips({ run }) {
  const took = duration(run.created_at, run.finished_at);
  return (
    <>
      <Chip Icon={Rows}>{count(run.cases)} cases</Chip>
      <Chip Icon={Lightning} title={`${count(run.totals.cached)} of these were cache hits`}>
        {count(run.totals.calls)} calls
        <span className="text-tertiary">· {count(run.totals.cached)} cached</span>
      </Chip>
      <Chip Icon={CurrencyDollar}>{usd(run.totals.cost_usd)}</Chip>
      {took && <Chip Icon={Timer}>{took}</Chip>}
    </>
  );
}

/** A score, or the word "failed" on danger soft when the scorer produced no value. */
function ScoreCell({ result }) {
  if (!result) return <Dash word="not run" />;
  if (result.score == null) {
    return (
      <Tag tone="danger" tip="failed: the scorer produced no value for this output">
        failed
      </Tag>
    );
  }
  return <span title={result.reason ?? undefined}>{score(result.score)}</span>;
}

function Compare({ api, a, b }) {
  const compare = useRequest(() => api.compare(a, b), [api, a, b]);
  // Run a's config carries the delta that decides what counts as "different".
  const runA = useRequest(() => api.experiment(a), [api, a]);
  const [filter, setFilter] = useState("all");
  const data = compare.data;
  const threshold = Number(runA.data?.config?.delta ?? 0.03);
  const caseRows = useMemo(
    () =>
      (data?.cases ?? []).filter(
        (r) => filter === "all" || (r.delta != null && Math.abs(r.delta) > threshold),
      ),
    [data, filter, threshold],
  );
  const scorerRows = data ? Object.entries(data.scorers).map(([key, v]) => ({ key, ...v })) : [];
  const nameOf = (run) => run.name ?? `#${run.id}`;

  const scorerColumns = data
    ? [
        { key: "key", label: "scorer", icon: Percent },
        { key: "a", label: nameOf(data.a), icon: Percent, align: "right", render: (r) => score(r.a) ?? <Dash /> },
        { key: "b", label: nameOf(data.b), icon: Percent, align: "right", render: (r) => score(r.b) ?? <Dash /> },
        { key: "delta", label: "delta", icon: Triangle, align: "right", render: (r) => <Delta value={r.delta} /> },
      ]
    : [];
  const caseColumns = data
    ? [
        { key: "index", label: "#", icon: Hash, align: "right", width: 48, muted: true },
        { key: "input", label: "input", icon: ArrowDownRight },
        { key: "a", label: nameOf(data.a), icon: Percent, align: "right", render: (r) => score(r.a) ?? <Dash /> },
        { key: "b", label: nameOf(data.b), icon: Percent, align: "right", render: (r) => score(r.b) ?? <Dash /> },
        { key: "delta", label: "delta", icon: Triangle, align: "right", render: (r) => <Delta value={r.delta} /> },
      ]
    : [];

  return (
    <Panel>
      <TitleRow
        title={data ? `${nameOf(data.a)} vs ${nameOf(data.b)}` : "Compare"}
        Icon={ArrowsLeftRight}
        crumb={{ label: "Experiments", to: "/experiments" }}
        loading={compare.loading}
        error={compare.error}
        chips={
          data && (
            <Chip Icon={Rows}>
              {filter === "all"
                ? `${count(data.cases.length)} cases`
                : `${count(caseRows.length)} of ${count(data.cases.length)} cases`}
            </Chip>
          )
        }
      >
        {data && (
          <span className="text-sm text-secondary">
            overall {score(data.a.score) ?? "–"} → {score(data.b.score) ?? "–"} (
            <Delta value={data.delta} />)
          </span>
        )}
        <SegmentedControl options={COMPARE_OPTIONS(threshold)} value={filter} onChange={setFilter} label="display" />
      </TitleRow>
      {data && (
        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
          <div className="px-5 pt-3 text-xs font-medium text-secondary">per scorer</div>
          <div className="max-h-56 shrink-0">
            <Table columns={scorerColumns} rows={scorerRows} rowKey={(r) => r.key} />
          </div>
          <div className="px-5 pt-4 text-xs font-medium text-secondary">per case</div>
          {caseRows.length > 0 && (
            <div className="flex shrink-0 flex-col gap-2 px-5 pt-3 pb-4">
              <div className="text-sm text-secondary">
                each case: {nameOf(data.a)} across, {nameOf(data.b)} up; on the diagonal nothing changed
              </div>
              <Scatter points={caseRows} threshold={threshold} nameA={nameOf(data.a)} nameB={nameOf(data.b)} />
            </div>
          )}
          {caseRows.length === 0 ? (
            <EmptyState
              Icon={ArrowsLeftRight}
              title="No rows match this filter"
              sentence={`No case moved by more than ±${threshold.toFixed(2)} between the two runs.`}
            />
          ) : (
            <Table columns={caseColumns} rows={caseRows} rowKey={(r) => r.index} rowHeight={40} />
          )}
        </div>
      )}
    </Panel>
  );
}

function Delta({ value }) {
  if (value == null) return <Dash />;
  const tone = value > 0 ? "text-ok" : value < 0 ? "text-danger" : "text-secondary";
  const word = value > 0 ? "higher under b" : value < 0 ? "lower under b" : "no change";
  return (
    <Tooltip text={`${delta(value)}: ${word}`}>
      <span className={tone}>{delta(value)}</span>
    </Tooltip>
  );
}

/** The display filter of the per-case table (DESIGN.md §7 SegmentedControl). */
function matchesFilter(row, filter) {
  if (filter === "failed") return row.failed;
  if (filter === "low") return Object.values(row.scores).some((s) => s.score != null && s.score < 0.5);
  return true;
}

/** One CSV row per table row: case, repeat, variant, input, output, expected, a score and a reason per scorer. */
function resultsCsv(rows, scorerKeys) {
  const columns = [
    { key: "case_index", label: "case" },
    { key: "repeat_index", label: "repeat" },
    { key: "variant_id", label: "variant", value: (r) => r.variant_id ?? "baseline" },
    { key: "input", label: "input" },
    { key: "output", label: "output" },
    { key: "expected", label: "expected" },
    ...scorerKeys.flatMap((key) => [
      { key: `score:${key}`, label: key, value: (r) => r.scores[key]?.score ?? "" },
      { key: `reason:${key}`, label: `${key} reason`, value: (r) => r.scores[key]?.reason ?? "" },
    ]),
  ];
  return toCsv(columns, rows);
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
