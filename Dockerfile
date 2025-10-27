# DBT MCP Server - Dockerfile
# This provides a unified environment for running DBT with BigQuery

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DBT_PROJECT_DIR=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files first (for better caching)
COPY requirements.txt .
COPY .env.example .

# Install Python dependencies using uv
RUN uv pip install --system -r requirements.txt

# Copy project files
COPY models/ ./models/
COPY macros/ ./macros/
COPY seeds/ ./seeds/
COPY analyses/ ./analyses/
COPY tests/ ./tests/
COPY dbt_project.yml .
COPY packages.yml .

# Copy agent files
COPY agents/ ./agents/
COPY app.py .

# Create directories for Google Cloud credentials
RUN mkdir -p /app/credentials

# Create .env file from example if it doesn't exist
RUN if [ ! -f .env ]; then cp .env.example .env; fi

# Set Google Application Credentials path (will be mounted as volume)
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json

# Expose Streamlit port
EXPOSE 8501

# Health check - verify dbt, google-cloud-bigquery, and streamlit are importable
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "from dbt.cli.main import dbtRunner; import google.cloud.bigquery; import streamlit" || exit 1

# Default command - run Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
