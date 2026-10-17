import { ArrowLeft, Scissors } from "@phosphor-icons/react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router";

import CutPromptPanel from "../ui/CutPromptPanel.jsx";
import Dash from "../ui/Dash.jsx";
import EmptyState from "../ui/EmptyState.jsx";
import { count, dateTime, score, usd } from "../ui/format.js";
import PaintedPrompt from "../ui/PaintedPrompt.jsx";
import Panel from "../ui/Panel.jsx";
import SegmentCard from "../ui/SegmentCard.jsx";
import SidePanel from "../ui/SidePanel.jsx";
import Slider from "../ui/Slider.jsx";
import StatTile from "../ui/StatTile.jsx";
import StatusTag from "../ui/StatusTag.jsx";
import Table from "../ui/Table.jsx";
import TitleRow from "../ui/TitleRow.jsx";
import { useRequest } from "../ui/useRequest.js";
import VerdictLegend from "../ui/VerdictLegend.jsx";
import { colourAt } from "../ui/verdictRule.js";

const RUN_COMMAND = "promptgauge ablate --config promptgauge.yaml";

/** F8.3. `/ablations` lists ablation runs; `/ablations/:id` is the painted prompt. */
export default function Ablation({ api }) {
  const { id } = useParams();
  return id ? <AblationDetail api={api} id={Number(id)} /> : <AblationList api={api} />;
}

function AblationList({ api }) {
  const navigate = useNavigate();
  const runs = useRequest(() => api.experiments("ablation"), [api]);
  const rows = runs.data ?? [];
  const columns = [
    { key: "name", label: "name", render: (r) => r.name ?? <Dash /> },
    { key: "model", label: "model" },
    { key: "score", label: "baseline", align: "right", render: (r) => score(r.score) ?? <Dash /> },
    { key: "cases", label: "cases", align: "right", render: (r) => count(r.cases) },
    { key: "calls", label: "calls", align: "right", sortValue: (r) => r.totals.calls, render: (r) => count(r.totals.calls) },
    { key: "cost", label: "cost", align: "right", sortValue: (r) => r.totals.cost_usd, render: (r) => usd(r.totals.cost_usd) },
    { key: "created_at", label: "date", render: (r) => dateTime(r.created_at) },
    { key: "status", label: "status", render: (r) => <StatusTag status={r.status} stoppedReason={r.stopped_reason} /> },
  ];
  return (
    <Panel>
      <TitleRow title="Ablations" loading={runs.loading} error={runs.error} />
      {!runs.loading && rows.length === 0 ? (
        <EmptyState Icon={Scissors} title="No ablations yet" command={RUN_COMMAND} />
      ) : (
        <Table columns={columns} rows={rows} rowKey={(r) => r.id} onRowClick={(r) => navigate(`/ablations/${r.id}`)} />
      )}
    </Panel>
  );
}

function AblationDetail({ api, id }) {
  const navigate = useNavigate();
  const ablation = useRequest(() => api.ablation(id), [api, id]);
  const settings = useRequest(() => api.settings(), [api]);
  const [delta, setDelta] = useState(null);
  const [pinnedId, setPinnedId] = useState(null);
  const [callsPerMonth, setCallsPerMonth] = useState(null);
  const [saveError, setSaveError] = useState(null);

  const data = ablation.data;
  useEffect(() => {
    if (data && delta === null) setDelta(data.delta);
  }, [data, delta]);
  useEffect(() => {
    if (settings.data && callsPerMonth === null) setCallsPerMonth(settings.data.calls_per_month);
  }, [settings.data, callsPerMonth]);

  const current = delta ?? data?.delta ?? 0.03;
  const counts = useMemo(() => countColours(data?.segments ?? [], current), [data, current]);
  const measured = (data?.segments ?? []).filter((s) => s.verdict).length;
  const total = data?.segments.length ?? 0;
  const pinned = (data?.segments ?? []).find((s) => s.id === pinnedId) ?? null;
  const baseline = data?.ablation?.baseline_score ?? null;
  const stopped = data?.experiment.status === "stopped" ? data.experiment.stopped_reason ?? "error" : null;
  const mostlyGrey = measured > 0 && counts.grey / measured > 0.8;

  const saveCalls = (value) => {
    setCallsPerMonth(value);
    setSaveError(null);
    api.updateSettings({ calls_per_month: value }).catch(setSaveError);
  };

  return (
    <>
      <Panel>
        <TitleRow
          title={
            <span className="flex items-center gap-2">
              <button type="button" onClick={() => navigate("/ablations")} aria-label="back to ablations" className="rounded-sm p-1 text-secondary hover:bg-surface-2">
                <ArrowLeft size={16} />
              </button>
              {data?.experiment.name ?? `Ablation ${id}`}
            </span>
          }
          loading={ablation.loading || settings.loading}
          error={ablation.error ?? settings.error ?? saveError}
        >
          {data && <StatusTag status={data.experiment.status} stoppedReason={data.experiment.stopped_reason} />}
          {data && <Slider value={current} onChange={setDelta} />}
        </TitleRow>
        {data && (
          <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
            {stopped && (
              <div className="mx-5 mt-4 rounded-sm bg-warn-soft px-3 py-2 text-sm">
                <span className="font-medium text-warn">Stopped: {stopped}.</span>{" "}
                {count(measured)} of {count(total)} segments measured; the cut prompt was not confirmed.
              </div>
            )}
            <div className="flex flex-wrap gap-2 px-5 pt-4">
              <StatTile label="segments" value={`${count(measured)} / ${count(total)}`} hint="measured" />
              <StatTile label="red · grey · green" value={`${counts.red} · ${counts.grey} · ${counts.green}`} hint={`at delta ${current.toFixed(2)}`} />
              <StatTile label="tokens" value={data.ablation ? `${count(data.ablation.tokens_before)} → ${count(data.ablation.tokens_after)}` : "–"} />
              <StatTile label="baseline" value={score(baseline) ?? "–"} />
              <StatTile label="cut" value={score(data.ablation?.cut_score) ?? "–"} hint={data.ablation ? (data.ablation.confirmed ? "confirmed" : "not confirmed") : "no confirmation run"} />
              <StatTile label="cost" value={usd(data.totals.cost_usd)} hint={`${count(data.totals.calls)} calls · ${count(data.totals.cached)} cached`} />
            </div>
            <div className="flex flex-col gap-2 px-5 pt-4">
              <VerdictLegend legend={data.legend} counts={counts} />
              {mostlyGrey && (
                <div className="text-sm">
                  <span className="font-medium text-warn">Most segments are grey:</span>{" "}
                  <span className="text-secondary">at this sample size the run cannot separate them from the baseline. More cases or repeats narrow the intervals.</span>
                </div>
              )}
            </div>
            <div className="px-5 py-4">
              <PaintedPrompt
                text={data.prompt_text}
                segments={data.segments}
                delta={current}
                legend={data.legend}
                baseline={baseline}
                pinnedId={pinnedId}
                onPin={setPinnedId}
              />
            </div>
            <CutPromptPanel
              promptText={data.prompt_text}
              ablation={data.ablation}
              delta={data.delta}
              inputUsdPerMillion={data.input_usd_per_million}
              callsPerMonth={callsPerMonth ?? settings.data?.calls_per_month ?? 100000}
              inrRate={settings.data?.inr_rate ?? 84}
              onCallsPerMonth={saveCalls}
              stopped={stopped}
            />
          </div>
        )}
      </Panel>
      {pinned && data && (
        <SidePanel title={`Segment ${pinned.level === "block" ? "block" : "line"} ${pinned.index + 1}`} subtitle="pinned; click the prompt background to unpin" onClose={() => setPinnedId(null)}>
          <SegmentCard
            segment={pinned}
            colour={colourAt(pinned, current)}
            legend={data.legend}
            baseline={baseline}
            blockIndexOf={(parentId) => (data.segments.filter((s) => s.level === "block").findIndex((s) => s.id === parentId) + 1) || "?"}
          />
        </SidePanel>
      )}
    </>
  );
}

function countColours(segments, delta) {
  const counts = { red: 0, grey: 0, green: 0, unmeasured: 0 };
  for (const segment of segments) counts[colourAt(segment, delta) ?? "unmeasured"]++;
  return counts;
}
