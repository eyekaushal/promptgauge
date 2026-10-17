import { GearSix } from "@phosphor-icons/react";
import { useEffect, useState } from "react";

import CodeBlock from "../ui/CodeBlock.jsx";
import EmptyState from "../ui/EmptyState.jsx";
import Panel from "../ui/Panel.jsx";
import Tag from "../ui/Tag.jsx";
import TitleRow from "../ui/TitleRow.jsx";
import { useRequest } from "../ui/useRequest.js";
import { configToYaml } from "../ui/yaml.js";

/**
 * F8.4: model, judge, budget_usd, delta from the config of the last run (else the promptgauge.yaml
 * `promptgauge ui` loaded); API key present / missing, never the key; calls_per_month and
 * inr_rate editable and saved through PUT /api/settings.
 */
export default function Settings({ api }) {
  const settings = useRequest(() => api.settings(), [api]);
  const runs = useRequest(() => api.experiments(), [api]);
  const lastId = runs.data?.[0]?.id ?? null;
  const last = useRequest(() => (lastId ? api.experiment(lastId) : null), [api, lastId]);

  // `current` is what the server holds; `draft` is what the inputs show.
  const [current, setCurrent] = useState(null);
  const [draft, setDraft] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    if (settings.data && current === null) {
      const values = { calls_per_month: settings.data.calls_per_month, inr_rate: settings.data.inr_rate };
      setCurrent(values);
      setDraft({ calls_per_month: String(values.calls_per_month), inr_rate: String(values.inr_rate) });
    }
  }, [settings.data, current]);

  const source = last.data ? "last run" : settings.data?.config ? "promptgauge.yaml" : null;
  const config = last.data?.config ?? settings.data?.config ?? null;
  const callsValid = Number.isInteger(Number(draft?.calls_per_month)) && Number(draft?.calls_per_month) >= 1;
  const rateValid = Number(draft?.inr_rate) > 0;
  const dirty =
    draft &&
    current &&
    (Number(draft.calls_per_month) !== current.calls_per_month ||
      Number(draft.inr_rate) !== current.inr_rate);

  const save = async () => {
    setSaving(true);
    setSaveError(null);
    setSaved(false);
    try {
      const body = await api.updateSettings({
        calls_per_month: Number(draft.calls_per_month),
        inr_rate: Number(draft.inr_rate),
      });
      setCurrent({ calls_per_month: body.calls_per_month, inr_rate: body.inr_rate });
      setDraft({ calls_per_month: String(body.calls_per_month), inr_rate: String(body.inr_rate) });
      setSaved(true);
    } catch (error) {
      setSaveError(error);
    } finally {
      setSaving(false);
    }
  };

  const loading = settings.loading || runs.loading || last.loading;
  return (
    <Panel>
      <TitleRow title="Settings" Icon={GearSix} loading={loading} error={settings.error ?? saveError}>
        {saved && !dirty && <span className="text-sm text-ok">saved</span>}
        <button
          type="button"
          onClick={save}
          disabled={!dirty || !callsValid || !rateValid || saving}
          className="btn btn-primary"
        >
          Save
        </button>
      </TitleRow>
      {settings.data && current && draft && (
        <div className="flex flex-col gap-8 overflow-y-auto p-5">
          <Section title="API key">
            <Row label="ANTHROPIC_API_KEY">
              {settings.data.api_key_present ? (
                <Tag tone="ok" tip="present: the shell that started promptgauge ui had the key exported">
                  present
                </Tag>
              ) : (
                <Tag tone="danger" tip="missing: export ANTHROPIC_API_KEY before running eval or ablate">
                  missing
                </Tag>
              )}
              <span className="text-sm text-secondary">
                read from the environment only; never stored, never shown
              </span>
            </Row>
          </Section>

          <Section title={source ? `Run config (from the ${source})` : "Run config"}>
            {config ? (
              <div className="max-w-2xl">
                <CodeBlock label="promptgauge.yaml" text={configToYaml(config)} numbered yaml />
              </div>
            ) : (
              <EmptyState
                Icon={GearSix}
                title="No run yet and no promptgauge.yaml next to the server"
                command="promptgauge eval --config promptgauge.yaml"
              />
            )}
          </Section>

          <Section title="Display">
            <Row label="calls per month">
              <input
                type="number"
                min={1}
                step={1000}
                value={draft.calls_per_month}
                onChange={(e) => setDraft({ ...draft, calls_per_month: e.target.value })}
                aria-label="calls per month"
                className={`h-8 w-36 rounded-sm border bg-panel px-2 text-base ${callsValid ? "border-line-strong" : "border-danger"}`}
              />
              <span className="text-sm text-secondary">for the money-saved figure on every ablation</span>
            </Row>
            <Row label="INR per USD">
              <input
                type="number"
                min={0.01}
                step={0.5}
                value={draft.inr_rate}
                onChange={(e) => setDraft({ ...draft, inr_rate: e.target.value })}
                aria-label="INR per USD"
                className={`h-8 w-36 rounded-sm border bg-panel px-2 text-base ${rateValid ? "border-line-strong" : "border-danger"}`}
              />
              <span className="text-sm text-secondary">fixed rate; config `inr_rate` is the default</span>
            </Row>
          </Section>
        </div>
      )}
    </Panel>
  );
}

function Section({ title, children }) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-lg font-medium">{title}</h2>
      {children}
    </section>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-40 text-xs font-medium text-secondary">{label}</span>
      {children}
    </div>
  );
}
