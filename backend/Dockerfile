FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (cached unless Dockerfile changes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better layer caching
# This layer will be cached unless requirements.txt changes
COPY requirements.txt .

# Install Python dependencies (this is the slowest step ~5-10 min for PyTorch)
# This layer will be reused if requirements.txt hasn't changed
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (this changes most frequently)
# Changes here won't invalidate the dependency cache above
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
