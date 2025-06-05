# 1) Use the official Python 3.12.7 slim image
FROM python:3.12.7-slim

# 2) Install system dependencies: Tesseract OCR, its dev headers, and Poppler utilities
RUN apt-get update && \
    apt-get install -y \
      tesseract-ocr \
      libtesseract-dev \
      poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# 3) Create and switch to the application directory
WORKDIR /app

# 4) Copy only requirements.txt first (leverages Docker cache if requirements.txt hasn’t changed)
COPY requirements.txt .

# 5) Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 6) Copy the rest of your application code into the image
COPY . .

# 7) Expose the port your app listens on
EXPOSE 8000

# 8) Start the application using Gunicorn with Uvicorn workers
CMD ["gunicorn", "-w", "3", "-k", "uvicorn.workers.UvicornWorker", "Server.main:app", "--bind", "0.0.0.0:8000"]
