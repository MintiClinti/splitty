# splitty

Split long-form YouTube audio into segment clips (MVP).

## Architecture
- `frontend/`: React + Vite app (URL input, job status, preview, export download)
- `backend/`: FastAPI API with background job runner and SQLite metadata store
- `audio_engine/`: isolated chapter/fallback segmentation + split/export logic
- `data/`: local runtime artifacts (`downloads`, `segments`, `exports`, `tmp`)

## MVP Features
- Submit YouTube URL
- Upload local audio/video files for hosted analysis
- Chapter-first splitting (metadata/description)
- Fallback silence/low-energy style segmentation via ffmpeg `silencedetect`
- Segment preview with start/end/name/strategy
- Export split clips + `timestamps.csv` + `timestamps.txt` as zip

## Ingestion Modes
- Local backend: paste a YouTube URL and let `yt-dlp` download audio
- Hosted backend: upload an audio/video file to avoid server-side YouTube auth issues

## Local setup
1. Backend dependencies:
   - `pip install -r backend/requirements.txt`
2. Frontend dependencies:
   - `cd frontend && npm install`
3. Required binaries on `PATH`:
   - `yt-dlp`
   - `ffmpeg`
   - `ffprobe`

## Run locally
- Backend:
  - `cd backend && python run.py`
- Frontend:
  - `cd frontend && npm run dev`

## API (MVP)
- `POST /api/v1/jobs`
- `GET /api/v1/jobs/{jobId}`
- `GET /api/v1/jobs/{jobId}/preview`
- `POST /api/v1/jobs/{jobId}/export`
- `GET /api/v1/jobs/{jobId}/export`
- `GET /api/v1/exports/{exportId}/download`
