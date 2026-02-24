# Fallout Wiki Crawler Docker Image

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Python dependencies first (for better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers with all system dependencies
# --with-deps automatically installs required system libraries
RUN playwright install --with-deps firefox chromium

# Copy application code (new structure)
COPY src/ ./src/
COPY scripts/ ./scripts/

# Set PYTHONPATH to include /app
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Default command
CMD ["python", "-m", "src.crawlers.main", "config.yaml"]



