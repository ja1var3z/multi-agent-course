# Python AI service — private on Fly's internal network.
FROM python:3.13-slim

WORKDIR /app

# Install deps first so this layer caches across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite cache lives on a Fly volume mounted at /data so it survives restarts.
ENV TRANSLATION_DB_PATH=/data/translations.db

EXPOSE 8000

# Bind host is configurable so the same image works in both places:
#  - Fly (default ::)  → reachable over the 6PN private network via <app>.internal
#  - Docker Compose     → set UVICORN_HOST=0.0.0.0 for the IPv4 bridge network
# exec keeps uvicorn as PID 1 so it receives SIGTERM for graceful shutdown.
CMD ["sh", "-c", "exec uvicorn app:app --host ${UVICORN_HOST:-::} --port 8000"]
