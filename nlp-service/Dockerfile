FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
# Using --no-cache-dir to keep image size small
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 5000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
