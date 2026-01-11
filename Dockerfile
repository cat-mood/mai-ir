# Fallout Wiki Crawler Docker Image

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (for better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY url_normalizer.py .
COPY db_manager.py .
COPY crawler.py .
COPY main.py .

# Make main.py executable
RUN chmod +x main.py

# Default command
CMD ["python", "main.py", "config.yaml"]



