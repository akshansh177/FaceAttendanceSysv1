from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import numpy as np
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import decrypt_embedding, encrypt_embedding
from app.models.models import FaceEmbedding
from app.services.embedding_index import get_embedding_index
from app.services.recognition_client import recognition_client


@dataclass
class MatchResult:
    employee_id: UUID | None
    score: float
    second_best_score: float
    ambiguous: bool
    used_faiss: bool


async def store_embeddings(
    db: AsyncSession, employee_id: UUID, embeddings: list[list[float]], model: str = "insightface"
) -> int:
    await db.execute(delete(FaceEmbedding).where(FaceEmbedding.employee_id == employee_id))
    count = 0
    for emb in embeddings:
        raw = np.array(emb, dtype=np.float32).tobytes()
        encrypted = encrypt_embedding(raw)
        db.add(
            FaceEmbedding(
                employee_id=employee_id,
                embedding_vector=encrypted,
                model=model,
                encrypted=True,
            )
        )
        count += 1
    return count


async def load_embeddings(db: AsyncSession, employee_id: UUID | None = None) -> list[tuple[UUID, np.ndarray, str]]:
    q = select(FaceEmbedding)
    if employee_id:
        q = q.where(FaceEmbedding.employee_id == employee_id)
    result = await db.execute(q)
    rows = result.scalars().all()
    out: list[tuple[UUID, np.ndarray, str]] = []
    for row in rows:
        data = row.embedding_vector
        if row.encrypted:
            data = decrypt_embedding(data)
        emb = recognition_client.embedding_from_bytes(data)
        out.append((row.employee_id, emb, row.model))
    return out


async def rebuild_embedding_index(db: AsyncSession, *, broadcast: bool = True) -> int:
    """Reload FAISS index from all face embeddings."""
    rows = await load_embeddings(db)
    flat: list[tuple[UUID, np.ndarray]] = [(eid, emb) for eid, emb, _ in rows]
    get_embedding_index().rebuild(flat)
    if broadcast:
        from app.services.index_sync import publish_index_reload

        try:
            await publish_index_reload()
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning("Index reload pub/sub skipped: %s", e)
    return len(flat)


def _linear_match(probe: np.ndarray, embeddings: list[tuple[UUID, np.ndarray, str]]) -> list[tuple[UUID, float]]:
    per_employee: dict[UUID, float] = {}
    for employee_id, emb, _ in embeddings:
        score = recognition_client.cosine_similarity(probe, emb)
        if employee_id not in per_employee or score > per_employee[employee_id]:
            per_employee[employee_id] = score
    return sorted(per_employee.items(), key=lambda x: x[1], reverse=True)


async def find_best_match(db: AsyncSession, probe_embedding: list[float]) -> MatchResult:
    from app.services.match_settings import get_effective_match_threshold

    settings = get_settings()
    match_threshold = await get_effective_match_threshold(db)
    probe = np.array(probe_embedding, dtype=np.float32)
    used_faiss = False
    ranked: list[tuple[UUID, float]] = []

    if settings.use_faiss_index:
        index = get_embedding_index()
        if index.size == 0:
            await rebuild_embedding_index(db)
        candidates = index.search(probe)
        ranked = [(c.employee_id, c.score) for c in candidates]
        used_faiss = True

    if not ranked:
        embeddings = await load_embeddings(db)
        ranked = _linear_match(probe, embeddings)
        used_faiss = False

    if not ranked:
        return MatchResult(None, -1.0, -1.0, False, used_faiss)

    best_employee, best_score = ranked[0]
    second_best = ranked[1][1] if len(ranked) > 1 else -1.0
    ambiguous = (
        len(ranked) > 1
        and best_score >= match_threshold
        and (best_score - second_best) < settings.match_margin
    )
    if ambiguous:
        return MatchResult(None, best_score, second_best, True, used_faiss)

    return MatchResult(best_employee, best_score, second_best, False, used_faiss)


async def get_face_status(db: AsyncSession, employee_id: UUID) -> dict:
    result = await db.execute(
        select(func.count(FaceEmbedding.id), FaceEmbedding.model)
        .where(FaceEmbedding.employee_id == employee_id)
        .group_by(FaceEmbedding.model)
    )
    rows = result.all()
    models = [r[1] for r in rows] if rows else []
    count_result = await db.execute(
        select(func.count()).select_from(FaceEmbedding).where(FaceEmbedding.employee_id == employee_id)
    )
    count = count_result.scalar() or 0
    return {"employee_id": employee_id, "embedding_count": count, "models": models}


def validate_enrollment_embeddings(embeddings: list[list[float]], models: list[str]) -> str | None:
    """Return error message if enrollment set fails quality checks."""
    settings = get_settings()
    if any(m == "fallback" for m in models):
        return "InsightFace model required; fallback embeddings not allowed for enrollment"
    if len(embeddings) < 2:
        return None
    vecs = [np.array(e, dtype=np.float32) for e in embeddings]
    min_pair = 1.0
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            sim = recognition_client.cosine_similarity(vecs[i], vecs[j])
            min_pair = min(min_pair, sim)
    if min_pair < settings.min_enrollment_pairwise_similarity:
        return "Enrollment images appear inconsistent (different people or poor angles)"
    return None
