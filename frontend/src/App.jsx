import { useEffect, useMemo, useState } from "react";
import { createExport, createUploadJob, getDownloadUrl, getExport, getJob, getPreview } from "./api/client";
import { SegmentTable } from "./components/SegmentTable";

export function App() {
  const [uploadFile, setUploadFile] = useState(null);
  const [chaptersFile, setChaptersFile] = useState(null);
  const [chaptersText, setChaptersText] = useState("");
  const [uploadTitle, setUploadTitle] = useState("");
  const [fileInputKey, setFileInputKey] = useState(0);
  const [chaptersFileInputKey, setChaptersFileInputKey] = useState(0);
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

  const resetForNewJob = () => {
    setError("");
    setPreview(null);
    setExportState(null);
    setNames([]);
    setJobId(null);
    setJobStatus(null);
  };

  const onUploadSubmit = async (event) => {
    event.preventDefault();
    if (!uploadFile) {
      setError("Choose an audio file to upload.");
      return;
    }
    resetForNewJob();
    try {
      const response = await createUploadJob(
        uploadFile,
        uploadTitle.trim(),
        chaptersText.trim(),
        chaptersFile,
      );
      setJobId(response.jobId);
      setJobStatus({ status: response.status });
      setUploadFile(null);
      setChaptersFile(null);
      setChaptersText("");
      setUploadTitle("");
      setFileInputKey((current) => current + 1);
      setChaptersFileInputKey((current) => current + 1);
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
      <p>Download audio locally, then upload the audio file with optional chapter text to preview and export splits.</p>

      <section className="panel">
        <h2>Upload Audio File</h2>
        <p className="hint">Run the local helper first if you want YouTube chapters preserved without asking the hosted backend to fetch media.</p>
        <p className="hint"><code>python3 scripts/download_youtube_local.py &lt;youtube-url&gt;</code></p>
        <form onSubmit={onUploadSubmit} className="stack-form">
          <input
            key={fileInputKey}
            type="file"
            accept="audio/*,video/mp4,video/webm,video/quicktime"
            onChange={(event) => setUploadFile(event.target.files?.[0] || null)}
            required
          />
          <input
            placeholder="Optional title"
            value={uploadTitle}
            onChange={(event) => setUploadTitle(event.target.value)}
          />
          <input
            key={chaptersFileInputKey}
            type="file"
            accept=".txt,text/plain"
            onChange={(event) => setChaptersFile(event.target.files?.[0] || null)}
          />
          <textarea
            placeholder="Optional chapter text (for example: 00:00 Intro)"
            value={chaptersText}
            onChange={(event) => setChaptersText(event.target.value)}
            rows={6}
          />
          <button type="submit">Upload and Analyze</button>
        </form>
      </section>

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
          <p><strong>Source:</strong> Uploaded file</p>
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
