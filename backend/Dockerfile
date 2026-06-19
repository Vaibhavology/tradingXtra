FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg2-binary (minimal) and general build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default port (overridden by Render's $PORT)
EXPOSE 8000

# Run with uvicorn — $PORT is injected by Render
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
