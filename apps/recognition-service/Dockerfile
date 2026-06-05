FROM python:3.12-slim AS builder

WORKDIR /app

# insightface builds Cython extensions; keep build tools in builder only
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

ENV OMP_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1

# Pre-download InsightFace weights at build time (avoids runtime OOM spike + first-request timeout)
RUN mkdir -p /root/.insightface/models && python -c "\
from insightface.app import FaceAnalysis; \
app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider']); \
app.prepare(ctx_id=0, det_size=(320, 320)); \
print('InsightFace buffalo_l ready')"

EXPOSE 6003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "6003", "--timeout-keep-alive", "120"]
