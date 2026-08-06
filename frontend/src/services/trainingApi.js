const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `HTTP error ${res.status}`);
  }
  return res.json();
}

export async function startTraining(file, randomSeed = 42) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('random_seed', randomSeed.toString());

  const res = await fetch(`${API_BASE}/train`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `HTTP error ${res.status}`);
  }

  return res.json();
}

export async function getJobStatus(jobId) {
  const res = await fetch(`${API_BASE}/status?job_id=${jobId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `HTTP error ${res.status}`);
  }
  return res.json();
}
