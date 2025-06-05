 FROM python:3.12.7-slim
     # Install Tesseract and other system dependencies
     RUN apt-get update && \
         apt-get install -y \
           tesseract-ocr \
           libtesseract-dev \
           poppler-utils \
         && rm -rf /var/lib/apt/lists/*

     # Set working directory
     WORKDIR /app

     # Copy requirements and install Python dependencies
     COPY requirements.txt .
     RUN pip install --no-cache-dir -r requirements.txt

     # Copy the application code
     COPY . .

     # Expose port (default to 8080)
     EXPOSE ${PORT:-8080}

     # Add a delay and run the application on the specified port
     CMD ["sh", "-c", "sleep 5 && gunicorn -w 3 -k uvicorn.workers.UvicornWorker Server.main:app --bind 0.0.0.0:${PORT:-8080}"]