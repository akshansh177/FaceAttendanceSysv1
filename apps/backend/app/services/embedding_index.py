from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from uuid import UUID

import numpy as np

from app.core.config import get_settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 512


@dataclass
class MatchCandidate:
    employee_id: UUID
    score: float


class EmbeddingIndex:
    """In-memory FAISS IndexFlatIP over L2-normalized 512-D embeddings."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._index = None
        self._employee_ids: list[UUID] = []
        self._version = 0
        self._last_rebuild_ms = 0.0

    @property
    def size(self) -> int:
        return len(self._employee_ids)

    @property
    def version(self) -> int:
        return self._version

    def rebuild(self, rows: list[tuple[UUID, np.ndarray]]) -> None:
        import faiss

        with self._lock:
            t0 = time.perf_counter()
            if not rows:
                self._index = None
                self._employee_ids = []
                self._version += 1
                return

            vectors = np.stack([r[1].astype(np.float32) for r in rows], axis=0)
            faiss.normalize_L2(vectors)
            index = faiss.IndexFlatIP(EMBEDDING_DIM)
            index.add(vectors)
            self._index = index
            self._employee_ids = [r[0] for r in rows]
            self._version += 1
            self._last_rebuild_ms = (time.perf_counter() - t0) * 1000
            logger.info("FAISS index rebuilt: %s vectors in %.1fms", len(rows), self._last_rebuild_ms)

    def search(self, probe: np.ndarray, top_k: int | None = None) -> list[MatchCandidate]:
        import faiss

        settings = get_settings()
        k = top_k or settings.faiss_top_k

        with self._lock:
            if self._index is None or not self._employee_ids:
                return []

            probe_v = probe.astype(np.float32).reshape(1, -1)
            faiss.normalize_L2(probe_v)
            k = min(k, len(self._employee_ids))
            scores, indices = self._index.search(probe_v, k)

        per_employee: dict[UUID, float] = {}
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0:
                continue
            emp_id = self._employee_ids[idx]
            s = float(score)
            if emp_id not in per_employee or s > per_employee[emp_id]:
                per_employee[emp_id] = s

        ranked = sorted(
            (MatchCandidate(employee_id=eid, score=sc) for eid, sc in per_employee.items()),
            key=lambda c: c.score,
            reverse=True,
        )
        return ranked


_index = EmbeddingIndex()


def get_embedding_index() -> EmbeddingIndex:
    return _index
