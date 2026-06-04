from __future__ import annotations

import logging

import cv2
import numpy as np

from app.engine import decode_image, get_insightface_app

logger = logging.getLogger(__name__)


def _native(val):
    """Convert numpy scalars to JSON-serializable Python types."""
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, (np.floating, float)):
        return float(val)
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, np.ndarray):
        return val.tolist()
    return val


def _face_center_and_scale(image_bytes: bytes) -> tuple[tuple[float, float] | None, list[float] | None]:
    app = get_insightface_app()
    img = decode_image(image_bytes)
    if app == "fallback":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0:
            return None, None
        x, y, fw, fh = faces[0]
        return (float(x + fw / 2), float(y + fh / 2)), [float(x), float(y), float(x + fw), float(y + fh)]

    faces = app.get(img)
    if not faces:
        return None, None
    face = faces[0]
    bbox = face.bbox.astype(float).tolist()
    if hasattr(face, "kps") and face.kps is not None:
        kps = np.array(face.kps)
        center = (float(kps[2, 0]), float(kps[2, 1])) if len(kps) > 2 else (
            float((bbox[0] + bbox[2]) / 2),
            float((bbox[1] + bbox[3]) / 2),
        )
        return center, bbox
    return (float((bbox[0] + bbox[2]) / 2), float((bbox[1] + bbox[3]) / 2)), bbox


def _laplacian_variance(image_bytes: bytes) -> float:
    img = decode_image(image_bytes)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def check_liveness(frames: list[bytes]) -> dict:
    if len(frames) < 3:
        return {"passed": False, "reason": "Need at least 3 frames", "checks": {}}

    centers: list[tuple[float, float]] = []
    bbox_scales: list[float] = []
    variances: list[float] = []

    for frame in frames:
        center, bbox = _face_center_and_scale(frame)
        if bbox is None:
            return {"passed": False, "reason": "No face detected — look at the camera", "checks": {}}
        variances.append(_laplacian_variance(frame))
        bbox_scales.append(max(bbox[2] - bbox[0], bbox[3] - bbox[1], 1.0))
        if center:
            centers.append(center)

    if max(variances) < 20:
        return {
            "passed": False,
            "reason": "Image too dark or blurry",
            "checks": {"blur": [_native(v) for v in variances]},
        }

    scale_ratio = float((max(bbox_scales) - min(bbox_scales)) / (np.mean(bbox_scales) + 1e-6))

    head_move = 0.0
    if len(centers) >= 2:
        deltas = [
            float(np.linalg.norm(np.array(centers[i]) - np.array(centers[i - 1])))
            for i in range(1, len(centers))
        ]
        head_move = float(np.mean(deltas))

    # Motion: head movement or face scale change between frames (proxy for blink/depth)
    motion_ok = head_move > 1.5 or scale_ratio > 0.008
    # Frame-to-frame variance (not a static photo)
    static_ok = float(np.std(variances)) > 0.5 or len({round(v, 0) for v in variances}) > 1

    passed = motion_ok and static_ok
    checks = {
        "head_movement": _native(head_move),
        "scale_ratio": _native(scale_ratio),
        "frame_variance": [_native(v) for v in variances],
        "motion_ok": _native(motion_ok),
        "static_ok": _native(static_ok),
    }
    return {
        "passed": _native(passed),
        "reason": None if passed else "Please move slightly and blink naturally",
        "checks": checks,
        "best_frame_index": int(np.argmax(variances)),
    }
