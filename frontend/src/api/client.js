const API_BASE = "http://127.0.0.1:8000/api/v1";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

export function createJob(youtubeUrl) {
  return request("/jobs", { method: "POST", body: JSON.stringify({ youtubeUrl }) });
}

export function getJob(jobId) {
  return request(`/jobs/${jobId}`);
}

export function getPreview(jobId) {
  return request(`/jobs/${jobId}/preview`);
}

export function createExport(jobId, names) {
  return request(`/jobs/${jobId}/export`, { method: "POST", body: JSON.stringify({ names }) });
}

export function getExport(jobId) {
  return request(`/jobs/${jobId}/export`);
}

export function getDownloadUrl(exportId) {
  return `${API_BASE}/exports/${exportId}/download`;
}
