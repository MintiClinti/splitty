# splitty

Split long-form audio into segment clips (MVP).

## Architecture
- `frontend/`: React + Vite app (file upload, job status, preview, export download)
- `backend/`: FastAPI API with background job runner and SQLite metadata store
- `audio_engine/`: chapter/fallback segmentation + split/export logic
- `data/`: local runtime artifacts (`downloads`, `segments`, `exports`, `tmp`)

## MVP Features
- Download YouTube audio locally, then upload it for hosted analysis
- Upload optional chapter text or a generated chapter sidecar to preserve chapter-based splits
- Chapter-first splitting (metadata/description)
- Fallback silence/low-energy style segmentation via ffmpeg `silencedetect`
- Segment preview with start/end/name/strategy
- Export split clips + `timestamps.csv` + `timestamps.txt` as zip

## Local setup
1. Backend dependencies:
   - `pip install -r backend/requirements.txt`
2. Frontend dependencies:
   - `cd frontend && npm install`
3. Required binaries on `PATH`:
   - `ffmpeg`
   - `ffprobe`
4. Optional local download helper:
   - `yt-dlp`

## Run locally
- Backend:
  - `cd backend && python run.py`
- Frontend:
  - `cd frontend && npm run dev`
- Local YouTube download helper:
  - `python3 scripts/download_youtube_local.py "https://youtube.com/watch?v=..."`
  - Upload the generated audio file and, if present, the matching `.chapters.txt` sidecar

## API (MVP)
- `POST /api/v1/jobs` (multipart upload: `file`, optional `title`, optional `chapters_text`, optional `chapters_file`)
- `GET /api/v1/jobs/{jobId}`
- `GET /api/v1/jobs/{jobId}/preview`
- `POST /api/v1/jobs/{jobId}/export`
- `GET /api/v1/jobs/{jobId}/export`
- `GET /api/v1/exports/{exportId}/download`
