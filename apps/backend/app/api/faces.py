from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import HR_ROLES, require_roles
from app.models.models import Employee, FaceEmbedding, User
from app.schemas.schemas import FaceEnrollResponse, FaceStatusResponse, MessageResponse
from app.services.audit import log_audit
from app.services.embedding_index import get_embedding_index
from app.services.face_service import (
    get_face_status,
    rebuild_embedding_index,
    store_embeddings,
    validate_enrollment_embeddings,
)
from app.services.recognition_client import RecognitionServiceError, recognition_client

router = APIRouter(prefix="/api/faces", tags=["faces"])


@router.post("/enroll", response_model=FaceEnrollResponse)
async def enroll_faces(
    employee_id: UUID = Query(...),
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(*HR_ROLES)),
):
    settings = get_settings()
    if len(files) < settings.min_enrollment_images:
        raise HTTPException(400, f"Minimum {settings.min_enrollment_images} images required")
    if len(files) > settings.max_enrollment_images:
        raise HTTPException(400, f"Maximum {settings.max_enrollment_images} images allowed")

    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Employee not found")

    embeddings: list[list[float]] = []
    models: list[str] = []
    for f in files:
        data = await f.read()
        try:
            resp = await recognition_client.detect_and_embed(data)
        except RecognitionServiceError as e:
            raise HTTPException(503, str(e)) from e
        if not resp or not resp.get("embedding"):
            raise HTTPException(400, f"No face detected in {f.filename}")
        if resp.get("model") == "fallback":
            raise HTTPException(400, f"Face model unavailable for {f.filename}; use clear front-facing photos")
        det = float(resp.get("det_score", 0))
        if det < settings.min_det_score:
            raise HTTPException(400, f"Low face detection confidence in {f.filename}")
        blur = float(resp.get("blur_variance", 0))
        if blur < settings.min_blur_variance:
            raise HTTPException(400, f"Image too blurry: {f.filename}")
        embeddings.append(resp["embedding"])
        models.append(resp.get("model", "insightface"))

    quality_err = validate_enrollment_embeddings(embeddings, models)
    if quality_err:
        raise HTTPException(400, quality_err)

    model_name = models[0] if models else "insightface"
    count = await store_embeddings(db, employee_id, embeddings, model=model_name)
    await db.commit()
    await rebuild_embedding_index(db)
    await log_audit(db, user.id, "face.enrolled", "face_embeddings", payload={"employee_id": str(employee_id), "count": count})
    return FaceEnrollResponse(
        employee_id=employee_id,
        embeddings_stored=count,
        message=f"Stored {count} face embeddings",
    )


@router.get("/{employee_id}", response_model=FaceStatusResponse)
async def face_status(
    employee_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    status = await get_face_status(db, employee_id)
    return FaceStatusResponse(**status)


@router.delete("/{employee_id}", response_model=MessageResponse)
async def delete_faces(
    employee_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    await db.execute(delete(FaceEmbedding).where(FaceEmbedding.employee_id == employee_id))
    await db.commit()
    await rebuild_embedding_index(db)
    await log_audit(db, user.id, "face.deleted", "face_embeddings", payload={"employee_id": str(employee_id)})
    return MessageResponse(message="Face embeddings deleted")


@router.post("/index/rebuild", response_model=MessageResponse)
async def rebuild_index(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    n = await rebuild_embedding_index(db)
    return MessageResponse(message=f"FAISS index rebuilt with {n} vectors (v{get_embedding_index().version})")
