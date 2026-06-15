FROM python:3.11-slim-bookworm

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY webapp/backend/requirements.txt /app/webapp/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/webapp/backend/requirements.txt

# We set PYTHONPATH to include /app, /app/cf, /app/cbf etc to resolve imports cleanly
ENV PYTHONPATH="/app:/app/cf:/app/cbf:${PYTHONPATH}"

EXPOSE 8000

CMD ["uvicorn", "webapp.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
