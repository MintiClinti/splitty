import { useEffect, useMemo, useState } from "react";
import { createExport, createJob, getDownloadUrl, getExport, getJob, getPreview } from "./api/client";
import { SegmentTable } from "./components/SegmentTable";

export function App() {
  const [url, setUrl] = useState("");
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [preview, setPreview] = useState(null);
  const [exportState, setExportState] = useState(null);
  const [names, setNames] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!jobId) return;
    const timer = setInterval(async () => {
      try {
        const status = await getJob(jobId);
        setJobStatus(status);
        if (status.status === "preview_ready" || status.status === "completed") {
          const previewData = await getPreview(jobId);
          setPreview(previewData);
          setNames(previewData.segments.map((segment) => segment.name));
        }
      } catch (err) {
        setError(err.message);
      }
    }, 1500);
    return () => clearInterval(timer);
  }, [jobId]);

  useEffect(() => {
    if (!jobId || !exportState || exportState.status === "completed" || exportState.status === "failed") {
      return;
    }
    const timer = setInterval(async () => {
      try {
        const next = await getExport(jobId);
        setExportState(next);
      } catch {
        // ignore transient state
      }
    }, 1500);
    return () => clearInterval(timer);
  }, [jobId, exportState]);

  const canExport = useMemo(() => preview?.segments?.length && jobStatus?.status === "preview_ready", [preview, jobStatus]);

  const onSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setPreview(null);
    setExportState(null);
    try {
      const response = await createJob(url.trim());
      setJobId(response.jobId);
      setJobStatus({ status: response.status });
    } catch (err) {
      setError(err.message);
    }
  };

  const onExport = async () => {
    if (!jobId || !preview) return;
    try {
      const response = await createExport(jobId, names);
      setExportState(response);
    } catch (err) {
      setError(err.message);
    }
  };

  const onNameChange = (index, value) => {
    setNames((current) => {
      const next = [...current];
      next[index] = value;
      return next;
    });
  };

  return (
    <main className="container">
      <h1>Splitty MVP</h1>
      <p>Paste a YouTube URL to split audio by chapters or fallback boundaries.</p>

      <form onSubmit={onSubmit} className="url-form">
        <input placeholder="https://youtube.com/watch?v=..." value={url} onChange={(event) => setUrl(event.target.value)} required />
        <button type="submit">Analyze</button>
      </form>

      {jobId && (
        <section className="panel">
          <h2>Job Status</h2>
          <p><strong>Job:</strong> {jobId}</p>
          <p><strong>Status:</strong> {jobStatus?.status || "pending"}</p>
          {jobStatus?.stage && <p><strong>Stage:</strong> {jobStatus.stage}</p>}
          {jobStatus?.progress != null && <p><strong>Progress:</strong> {jobStatus.progress}%</p>}
          {jobStatus?.error && <p className="error">{jobStatus.error}</p>}
        </section>
      )}

      {preview && (
        <section className="panel">
          <h2>Preview</h2>
          <p><strong>Video:</strong> {preview.video.title || "Untitled"}</p>
          <SegmentTable segments={preview.segments} names={names} onNameChange={onNameChange} />
          <button onClick={onExport} disabled={!canExport}>Export zip</button>
        </section>
      )}

      {exportState && (
        <section className="panel">
          <h2>Export</h2>
          <p><strong>Status:</strong> {exportState.status}</p>
          {exportState.error && <p className="error">{exportState.error}</p>}
          {exportState.status === "completed" && <a href={getDownloadUrl(exportState.exportId)}>Download Zip</a>}
        </section>
      )}

      {error && <p className="error">{error}</p>}
    </main>
  );
}
