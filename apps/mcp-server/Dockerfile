# Development stage - with watchdog for auto-reload
FROM python:3.13-slim AS development

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv and watchdog
RUN pip install --no-cache-dir uv watchdog[watchmedo]

# Copy project files (including README.md required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen

# Install Playwright browsers (required for DAA scraping)
RUN uv run playwright install --with-deps chromium

# Copy source code (will be overridden by volume in dev mode)
COPY . .

# Expose MCP server port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1

# Use watchmedo for auto-restart on file changes
CMD ["watchmedo", "auto-restart", "--directory=./", "--pattern=*.py", "--recursive", "--", "uv", "run", "python", "main.py"]

# Production stage - optimized
FROM python:3.13-slim AS production

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

# Install Playwright browsers with all dependencies
# Using --with-deps to ensure all Chromium dependencies are installed
RUN uv run playwright install --with-deps chromium

# Copy source code
COPY . .

# Expose MCP server port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"]