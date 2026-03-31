# ── Build stage ───────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Create app directories
RUN mkdir -p /app/uploads /app/logs && \
    chown -R appuser:appuser /app

# Copy application source and migration scripts
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser migrations/ /migrations/
COPY --chown=appuser:appuser scripts/ ./scripts/

# Streamlit config
RUN mkdir -p /home/appuser/.streamlit
COPY --chown=appuser:appuser <<'EOF' /home/appuser/.streamlit/config.toml
[server]
headless = true
address = "0.0.0.0"
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#3498db"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
EOF

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start command
CMD ["python", "-m", "streamlit", "run", "app/main.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]
