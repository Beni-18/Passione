// Fetch only; zero logic. Renders exactly what the API returns and nothing
// it infers itself — the grounding decision, the score, the metrics are all
// computed server-side. This file never fabricates a score client-side.

const API_BASE = window.PASSIONE_API_BASE || "http://localhost:8000";

const form = document.getElementById("predict-form");
const resultEl = document.getElementById("result");
const metricsEl = document.getElementById("metrics");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(form);

  const payload = {
    title: data.get("title"),
    genre: data.get("genre"),
    duration_minutes: Number(data.get("duration_minutes")),
    upload_time: new Date(data.get("upload_time")).toISOString(),
    language: data.get("language"),
    tags: (data.get("tags") || "")
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean),
  };

  const response = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json();
  renderResult(body);
});

function renderResult(body) {
  if (!body.grounded) {
    // The ungrounded case is rendered just as prominently as the grounded
    // one — a blank box here would be a bug, per docs/INTEGRATION.md.
    resultEl.textContent = `Not confidently scored: ${body.reason ?? "unknown reason"}`;
    return;
  }
  resultEl.textContent = `Trending probability: ${body.trending_probability} (model ${body.model_version})`;
}

async function loadMetrics() {
  const response = await fetch(`${API_BASE}/metrics`);
  if (!response.ok) {
    metricsEl.textContent = "No metrics available yet — no model is trained.";
    return;
  }
  const body = await response.json();
  metricsEl.textContent = `roc_auc=${body.roc_auc} precision=${body.precision} recall=${body.recall}`;
}

loadMetrics();
