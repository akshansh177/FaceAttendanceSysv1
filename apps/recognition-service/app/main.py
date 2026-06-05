from __future__ import annotations

import logging
import time

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from prometheus_client import Counter, Histogram, make_asgi_app

from app.engine import detect_and_embed_insightface, model_status, verify_deepface
from app.liveness import check_liveness

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Face Recognition Service", version="1.0.0")

RECOGNITION_LATENCY = Histogram(
    "recognition_duration_seconds",
    "Recognition endpoint latency",
    ["endpoint"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
)
LIVENESS_FAILURES = Counter("liveness_failures_total", "Liveness check failures")
MATCH_SCORE = Histogram("match_score", "Verification match scores", buckets=(0.5, 0.6, 0.7, 0.8, 0.9, 1.0))

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    if request.url.path.startswith("/detect-embed"):
        RECOGNITION_LATENCY.labels(endpoint="detect_embed").observe(time.perf_counter() - start)
    elif request.url.path.startswith("/liveness-check"):
        RECOGNITION_LATENCY.labels(endpoint="liveness").observe(time.perf_counter() - start)
    return response


@app.on_event("startup")
async def startup():
    from app.engine import get_insightface_app
    get_insightface_app()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "recognition", "model": model_status()}


@app.post("/detect-embed")
async def detect_embed(file: UploadFile = File(...)):
    data = await file.read()
    try:
        result = detect_and_embed_insightface(data)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        logging.exception("detect-embed failed")
        raise HTTPException(500, f"Face detection failed: {e}") from e
    if result is None:
        raise HTTPException(400, "No face detected")
    if result.get("error") == "multiple_faces":
        raise HTTPException(400, "Multiple faces detected")
    return result


@app.post("/liveness-check")
async def liveness_check(files: list[UploadFile] = File(...)):
    frames = [await f.read() for f in files]
    result = check_liveness(frames)
    if not result.get("passed"):
        LIVENESS_FAILURES.inc()
    return result


@app.post("/verify-deepface")
async def verify(probe: UploadFile = File(...), reference: UploadFile = File(...)):
    probe_data = await probe.read()
    ref_data = await reference.read()
    out = verify_deepface(probe_data, ref_data)
    if out.get("distance") is not None:
        MATCH_SCORE.observe(max(0.0, 1.0 - float(out["distance"])))
    return out
