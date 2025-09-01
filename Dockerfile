FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install build dependencies for nsjail
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    flex \
    bison \
    libprotobuf-dev \
    protobuf-compiler \
    libnl-3-dev \
    libnl-genl-3-dev \
    libnl-route-3-dev \
    libcap-dev \
    libseccomp-dev \
    && rm -rf /var/lib/apt/lists/*

# Build and install nsjail from source
RUN cd /tmp && \
    git clone --depth 1 --branch 3.4 https://github.com/google/nsjail.git && \
    cd nsjail && \
    make && \
    cp nsjail /usr/local/bin/ && \
    chmod +x /usr/local/bin/nsjail && \
    cd / && rm -rf /tmp/nsjail

# Verify nsjail installation
RUN which nsjail && nsjail --help | head -1

# Create nsjail config directory
RUN mkdir -p /etc/nsjail

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy nsjail configuration
COPY nsjail.cfg /etc/nsjail/nsjail.cfg

# Copy application code
COPY app.py .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "60", "app:app"] 