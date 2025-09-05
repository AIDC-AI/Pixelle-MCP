# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY pixelle/ ./pixelle/
COPY workflows/ ./workflows/
COPY docs/ ./docs/

# Install Python dependencies using uv
RUN uv sync --frozen

# Create pixelle working directory and data structure
WORKDIR /app
RUN mkdir -p /app/data/custom_workflows /app/data/custom_starters

# Set default port
ENV PORT=9004

# Expose port
EXPOSE 9004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9004/health || exit 1

# Run the application
CMD ["uv", "run", "pixelle", "start"]
