from __future__ import annotations

import httpx
import numpy as np

from app.core.config import get_settings


class RecognitionServiceError(Exception):
    """Recognition service unreachable or returned an error."""


class RecognitionClient:
    def __init__(self) -> None:
        self.base_url = get_settings().recognition_service_url.rstrip("/")

    async def liveness_check(self, frames: list[bytes]) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                files = [("files", (f"frame{i}.jpg", data, "image/jpeg")) for i, data in enumerate(frames)]
                resp = await client.post(f"{self.base_url}/liveness-check", files=files)
                if resp.status_code != 200:
                    detail = resp.text[:200] if resp.text else f"HTTP {resp.status_code}"
                    return {
                        "passed": False,
                        "reason": f"Liveness service error ({detail}). Is recognition running on port 6003?",
                    }
                return resp.json()
        except httpx.ConnectError:
            return {
                "passed": False,
                "reason": "Recognition service not reachable. Start: cd apps/recognition-service && uvicorn app.main:app --port 6003",
            }

    async def detect_and_embed(self, image_bytes: bytes) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
                resp = await client.post(f"{self.base_url}/detect-embed", files=files)
                if resp.status_code == 400:
                    return None
                if resp.status_code != 200:
                    detail = resp.text[:200] if resp.text else f"HTTP {resp.status_code}"
                    raise RecognitionServiceError(
                        f"Recognition service error: {detail}. "
                        f"Check: docker compose ps recognition && docker compose logs recognition --tail 20"
                    )
                return resp.json()
        except httpx.TimeoutException as e:
            raise RecognitionServiceError(
                "Recognition service timed out (model may still be loading). Retry in 30s."
            ) from e
        except httpx.RequestError as e:
            raise RecognitionServiceError(
                f"Recognition service crashed or disconnected at {self.base_url} "
                f"({e.__class__.__name__}). "
                "Run: docker compose logs recognition --tail 30 && docker compose up -d recognition"
            ) from e

    async def deepface_verify(
        self, probe_bytes: bytes, reference_bytes: bytes
    ) -> dict | None:
        settings = get_settings()
        if not settings.deepface_enabled:
            return None
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {
                "probe": ("probe.jpg", probe_bytes, "image/jpeg"),
                "reference": ("ref.jpg", reference_bytes, "image/jpeg"),
            }
            resp = await client.post(f"{self.base_url}/verify-deepface", files=files)
            if resp.status_code != 200:
                return None
            return resp.json()

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        a_norm = np.linalg.norm(a)
        b_norm = np.linalg.norm(b)
        if a_norm == 0 or b_norm == 0:
            return 0.0
        return float(np.dot(a, b) / (a_norm * b_norm))

    async def verify_deepface(self, probe_bytes: bytes, reference_bytes: bytes) -> dict | None:
        return await self.deepface_verify(probe_bytes, reference_bytes)

    @staticmethod
    def embedding_from_bytes(data: bytes) -> np.ndarray:
        return np.frombuffer(data, dtype=np.float32)


recognition_client = RecognitionClient()
