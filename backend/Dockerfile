FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (includes data/, app/, main.py, etc.)
COPY . .

# HuggingFace Spaces (Docker SDK) sends traffic to port 7860 by default.
# Honor $PORT if set so the same image works on other platforms.
ENV PORT=7860
EXPOSE 7860

# Run the application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]
