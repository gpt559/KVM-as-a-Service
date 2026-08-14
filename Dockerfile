# Use an official Python runtime as a parent image
FROM python:3.14-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Upgrade pip and install uv
RUN pip install --upgrade pip && pip install uv==0.9.26

# Install any needed packages specified in requirements.txt using uv
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY src/ ./src/
COPY static/ ./static/

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Healthcheck: parse the JSON body — HTTP 200 alone is not sufficient because the API
# always returns 200 even when the serial link is dead; the "status" field in the body
# is the real signal ("healthy" = port open, "unhealthy" = reconnect failed).
# "degraded" is also treated as failure: it means the port dropped and the background
# reconnect loop has not yet recovered it; requiring "healthy" is fail-safe and the loop
# (~5 s cadence) will pull the container back to healthy without manual intervention.
# curl/wget are not in the image; urllib.request is stdlib.
#
# Tuning rationale (Pi 5, cold-boot / power-cut scenario):
#   start-period 60 s — Linux boot + Docker daemon + USB-serial adapter enumeration can
#                        take ~40-50 s on a cold Pi 5; probe failures before this window
#                        closes do not count against retries.
#   interval     30 s — detects a broken link within ~30 s; at this cadence uvicorn logs
#                        ~2 access-log lines/min (~12 KB/hr), negligible vs. 10 MB ring.
#   timeout       5 s — generous for a loaded Pi; the urlopen call carries its own
#                        matching timeout so the probe never hangs past HEALTHCHECK timeout.
#   retries        3  — 3 × 30 s = 90 s of consecutive failure before Docker marks the
#                        container unhealthy; gives the reconnect loop ~18 attempts (at
#                        5 s each) to recover on its own before the container is flagged.
#
# NOTE: uvicorn access logging WILL record one entry per probe. This is intentional —
#       disabling access logs would also hide real request traffic. The volume is tiny.
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD ["python", "-c", "import urllib.request,json,sys; r=urllib.request.urlopen('http://localhost:8000/api/v1/status',timeout=5); d=json.loads(r.read()); sys.exit(0 if d.get('status')=='healthy' else 1)"]

# Run the application using uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
