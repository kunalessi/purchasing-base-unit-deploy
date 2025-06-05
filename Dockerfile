# ---------- Base ----------
FROM python:3.12-slim

# ---------- System deps ----------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        libtesseract-dev \
        poppler-utils && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ---------- Python deps ----------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- App ----------
COPY . .

# Optional, documents the public port Render uses
EXPOSE 10000

# ---------- Launch ----------
# • Bind to 0.0.0.0 so traffic from outside the container is accepted
# • Bind to $PORT so Render's health-check sees the server instantly
CMD ["gunicorn", "Server.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "3", "--bind", "0.0.0.0:$PORT"]
