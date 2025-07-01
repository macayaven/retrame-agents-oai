# Multi-stage Dockerfile for Reframe Edge API
# Stage 1: Builder
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all necessary files
COPY pyproject.toml ./
COPY uv.lock ./
COPY README.md ./
COPY app/ ./app/

# Install uv for faster dependency installation
RUN pip install uv

# Create virtual environment and install dependencies
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -e .

# Stage 2: Runtime
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application from builder
COPY --from=builder /app /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080
ENV ENVIRONMENT=production

# Set working directory
WORKDIR /app

# Expose port
EXPOSE 8080

# Activate virtual environment and run the application
ENTRYPOINT ["/app/.venv/bin/python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]