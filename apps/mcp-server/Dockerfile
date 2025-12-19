FROM python:3.13-slim

WORKDIR /app

# Install system dependencies and uv in one layer, cleanup immediately
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && pip install --no-cache-dir uv \
    && rm -rf /var/lib/apt/lists/*

# Copy project files (including README.md required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies and cleanup uv cache in one layer
RUN uv sync --frozen --no-cache

# Install Playwright browsers (required for DAA scraping)
# This downloads Chromium (~200MB) but necessary for crawl4ai
RUN uv run playwright install --with-deps chromium

# Copy source code (will be overridden by volume in dev mode)
COPY . .

# Expose MCP server port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"]