FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Python 3.12 (default on Ubuntu 24.04)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 python3.12-venv python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Docker CLI (para usar docker compose desde el devcontainer)
RUN curl -fsSL https://get.docker.com | bash - \
    && rm -rf /var/lib/apt/lists/* \
    && usermod -aG docker vscode

# Convenience symlinks
RUN ln -sf /usr/bin/python3.12 /usr/local/bin/python3 && \
    ln -sf /usr/bin/python3.12 /usr/local/bin/python && \
    ln -sf /usr/bin/pip3 /usr/local/bin/pip
