const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api/v1";

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

export function createUploadJob(file, title, chaptersText) {
  const body = new FormData();
  body.append("file", file);
  if (title) body.append("title", title);
  if (chaptersText) body.append("chapters_text", chaptersText);
  return request("/jobs", { method: "POST", body });
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
