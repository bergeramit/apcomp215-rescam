# Use the specified base image
FROM python:3.11-slim-bookworm

# Update package lists and install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and set up the working directory
RUN useradd -m app && \
    mkdir -p /app && \
    chown app:app /app

# Switch to non-root user
USER app

# Set the working directory
WORKDIR /app

# Copy the pyproject.toml for uv sync to download all necessary dependencies
COPY --chown=app:app pyproject.toml .

# Install uv, create venv, and install requirements
ENV PATH="/home/app/.local/bin:$PATH"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && uv sync

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"

# Copy the content of the local src directory to the working directory
COPY --chown=app:app dataloader.py .
COPY --chown=app:app preprocess_clean.py .

# Set the entrypoint and default command
ENTRYPOINT ["/bin/bash"]
CMD ["-c", "source /app/.venv/bin/activate && exec bash"]
