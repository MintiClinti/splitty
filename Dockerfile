FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir yt-dlp

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY audio_engine/ ./audio_engine/

ARG YT_COOKIES_B64=""
RUN if [ -n "$YT_COOKIES_B64" ]; then echo "$YT_COOKIES_B64" | base64 -d > /app/yt_cookies.txt; fi

ENV PYTHONPATH=/app:/app/backend
ENV YT_COOKIES_PATH=/app/yt_cookies.txt
WORKDIR /app/backend
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]