# ---------- Base image ----------
FROM python:3.12-slim

# ---------- System packages ----------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr libtesseract-dev poppler-utils && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ---------- Python packages ----------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Application code ----------
COPY . .

# (Optional) documents the public port Render injects
EXPOSE 10000

# ---------- Start ----------
# shell-form so $PORT expands; default to 10000 if Render ever omits it
CMD sh -c 'gunicorn Server.main:app \
           -k uvicorn.workers.UvicornWorker \
           -w "${WEB_CONCURRENCY:-3}" \
           --bind "0.0.0.0:${PORT:-10000}"'
