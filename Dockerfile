# This file is part of DisMu.
# Licensed under the GNU GPL v3 or later – see LICENSE.md for details.

# Choosing last Ubuntu LTS since it's faster than python base image
FROM ubuntu:24.04 AS builder-image

# Avoid stuck build due to user prompt
ARG DEBIAN_FRONTEND=noninteractive

# Installing needed dependencies during build
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3.12 -m venv /home/dismu/venv
ENV PATH="/home/dismu/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel
RUN pip install --no-cache-dir -r requirements.txt

FROM ubuntu:24.04 AS runner-image

# Installing needed dependencies during run
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    python3.12 \
    python3.12-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create user first
RUN useradd --create-home dismu

# Copy virtual environment from builder
COPY --from=builder-image /home/dismu/venv /home/dismu/venv

# Set up directories and copy application code
RUN mkdir -p /home/dismu/app
WORKDIR /home/dismu/app

# Copy the entire src directory to maintain proper structure
COPY src/ ./src/
COPY .env .

# Change ownership to dismu user
RUN chown -R dismu:dismu /home/dismu/app

# Switch to non-root user
USER dismu

# Virtual env settings
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/home/dismu/venv
ENV PATH="/home/dismu/venv/bin:$PATH"
ENV PYTHONPATH="/home/dismu/app"

# Command to run bot
CMD ["python", "src/main.py"]