from __future__ import annotations

import logging
from functools import lru_cache

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# 320 uses less RAM than 640 — important on small VPS (Contabo, etc.)
DET_SIZE = (320, 320)

_insightface_app = None
_deepface_available = True


def model_status() -> str:
    app = get_insightface_app()
    return "fallback" if app == "fallback" else "insightface"


def get_insightface_app():
    global _insightface_app
    if _insightface_app is None:
        try:
            from insightface.app import FaceAnalysis

            app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
            app.prepare(ctx_id=0, det_size=DET_SIZE)
            _insightface_app = app
            logger.info("InsightFace model loaded (det_size=%s)", DET_SIZE)
        except Exception as e:
            logger.warning("InsightFace unavailable, using fallback: %s", e)
            _insightface_app = "fallback"
    return _insightface_app


def decode_image(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image")
    return img


def detect_and_embed_insightface(image_bytes: bytes) -> dict | None:
    app = get_insightface_app()
    img = decode_image(image_bytes)

    if app == "fallback":
        return _fallback_embed(img)

    faces = app.get(img)
    if not faces:
        return None
    if len(faces) > 1:
        return {"error": "multiple_faces"}

    face = faces[0]
    embedding = face.embedding.astype(np.float32)
    embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
    bbox = face.bbox.astype(float).tolist()
    x1, y1, x2, y2 = [int(v) for v in face.bbox]
    x1, y1 = max(0, x1), max(0, y1)
    crop = img[y1:y2, x1:x2] if x2 > x1 and y2 > y1 else img
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
    blur_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return {
        "embedding": embedding.tolist(),
        "bbox": bbox,
        "det_score": float(face.det_score) if hasattr(face, "det_score") else 1.0,
        "blur_variance": blur_var,
        "model": "insightface",
    }


def _fallback_embed(img: np.ndarray) -> dict:
    """Simple histogram-based fallback when InsightFace models unavailable."""
    resized = cv2.resize(img, (64, 64))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [32], [0, 256]).flatten()
    hist = hist.astype(np.float32)
    hist = hist / (np.linalg.norm(hist) + 1e-8)
    padded = np.zeros(512, dtype=np.float32)
    padded[: len(hist)] = hist
    blur_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return {
        "embedding": padded.tolist(),
        "bbox": [0, 0, img.shape[1], img.shape[0]],
        "det_score": 0.5,
        "blur_variance": blur_var,
        "model": "fallback",
    }


def verify_deepface(probe_bytes: bytes, reference_bytes: bytes) -> dict:
    global _deepface_available
    if not _deepface_available:
        return {"verified": False, "distance": 1.0, "model": "none"}

    try:
        from deepface import DeepFace
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as p1:
            p1.write(probe_bytes)
            probe_path = p1.name
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as p2:
            p2.write(reference_bytes)
            ref_path = p2.name

        try:
            result = DeepFace.verify(
                img1_path=probe_path,
                img2_path=ref_path,
                model_name="Facenet",
                enforce_detection=False,
                detector_backend="opencv",
            )
            return {
                "verified": bool(result.get("verified")),
                "distance": float(result.get("distance", 1.0)),
                "threshold": float(result.get("threshold", 0.4)),
                "model": "deepface_facenet",
            }
        finally:
            os.unlink(probe_path)
            os.unlink(ref_path)
    except Exception as e:
        logger.warning("DeepFace verify failed: %s", e)
        _deepface_available = False
        return {"verified": False, "distance": 1.0, "error": str(e), "model": "deepface"}
