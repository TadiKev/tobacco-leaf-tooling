# ./ml/Dockerfile
FROM tensorflow/tensorflow:2.15.0

WORKDIR /workspace

# Small runtime dependencies for FastAPI + JPEG support
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libjpeg-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*

# Copy python dependencies
COPY requirements.txt /workspace/requirements.txt

# Ensure FastAPI + Uvicorn are installed even if missing in requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /workspace/requirements.txt \
    && pip install --no-cache-dir fastapi uvicorn[standard] requests pillow numpy

# Copy the inference server and any helpers
COPY serve.py /workspace/serve.py
# Optional: COPY other helper modules, e.g., COPY utils.py /workspace/utils.py

# Expose the port for uvicorn
EXPOSE 8000

# Start FastAPI server
CMD ["python", "-m", "uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8000"]
