# ---- single-stage image: FastAPI backend + static frontend ----
# Plain HTML/CSS/JS needs no build step, so one stage is enough.
FROM python:3.12-slim

# Build tools, in case any dependency has no prebuilt wheel and must compile.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first so this layer is cached unless requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application (respects .dockerignore).
COPY . .

# Azure Container Apps routes external traffic to this port.
EXPOSE 8000

# Start the web server. 0.0.0.0 makes it reachable from outside the container.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
