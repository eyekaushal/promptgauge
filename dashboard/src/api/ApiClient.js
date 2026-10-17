import { ApiError } from "./ApiError.js";

/**
 * One method per route of PRD §13. The dashboard never calls a model and never writes anything
 * but the display settings (invariant 6); this is the only file that talks to the server.
 */
export class ApiClient {
  constructor(baseUrl = "/api", fetchFn = globalThis.fetch.bind(globalThis)) {
    this._base = baseUrl;
    this._fetch = fetchFn;
  }

  health() {
    return this._get("/health");
  }

  datasets() {
    return this._get("/datasets");
  }

  cases(datasetHash) {
    return this._get(`/datasets/${encodeURIComponent(datasetHash)}/cases`);
  }

  experiments(kind) {
    return this._get(kind ? `/experiments?kind=${encodeURIComponent(kind)}` : "/experiments");
  }

  experiment(id) {
    return this._get(`/experiments/${id}`);
  }

  results(id) {
    return this._get(`/experiments/${id}/results`);
  }

  compare(a, b) {
    return this._get(`/experiments/compare?a=${a}&b=${b}`);
  }

  ablation(id) {
    return this._get(`/ablations/${id}`);
  }

  settings() {
    return this._get("/settings");
  }

  updateSettings(body) {
    return this._send("PUT", "/settings", body);
  }

  _get(path) {
    return this._send("GET", path);
  }

  async _send(method, path, body) {
    const init = { method, headers: { accept: "application/json" } };
    if (body !== undefined) {
      init.headers["content-type"] = "application/json";
      init.body = JSON.stringify(body);
    }
    const response = await this._fetch(this._base + path, init);
    const text = await response.text();
    let payload = null;
    try {
      payload = text ? JSON.parse(text) : null;
    } catch {
      payload = null;
    }
    if (!response.ok) {
      throw new ApiError(response.status, describe(response.status, payload));
    }
    return payload;
  }
}

function describe(status, payload) {
  if (status === 403) return "refused: open the dashboard at 127.0.0.1:7331";
  const detail = payload && payload.detail;
  if (typeof detail === "string") return detail;
  // Pydantic's 422 body is a list of {loc, msg}; one line per field, as the CLI does it.
  if (Array.isArray(detail)) {
    return detail.map((e) => `${(e.loc || []).slice(1).join(".")}: ${e.msg}`).join("; ");
  }
  return `request failed (${status})`;
}
