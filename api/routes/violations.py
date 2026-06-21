"""Violation list, image, update, delete routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import ViolationResponse, ViolationUpdate
from api.storage import get_storage
from database.models import Violation

router = APIRouter(prefix="/api/violations", tags=["violations"])


@router.get("", response_model=list[ViolationResponse])
def list_violations(
    db: Session = Depends(get_db),
    plate: str | None = Query(None),
    video_id: str | None = Query(None),
    reviewed: bool | None = Query(None),
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
):
    q = db.query(Violation)
    if plate:
        q = q.filter(Violation.plate_number.ilike(f"%{plate}%"))
    if video_id:
        q = q.filter(Violation.video_id == video_id)
    if reviewed is not None:
        q = q.filter(Violation.reviewed == reviewed)
    if from_date:
        q = q.filter(Violation.created_at >= from_date)
    if to_date:
        q = q.filter(Violation.created_at <= to_date)
    return q.order_by(Violation.created_at.desc()).all()


@router.get("/{violation_id}", response_model=ViolationResponse)
def get_violation(violation_id: int, db: Session = Depends(get_db)):
    violation = db.query(Violation).filter(Violation.id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    return violation


@router.get("/{violation_id}/image")
def get_violation_image(violation_id: int, db: Session = Depends(get_db)):
    violation = db.query(Violation).filter(Violation.id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    storage = get_storage()
    try:
        data = storage.read(violation.evidence_image_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Evidence image not found") from None

    return Response(content=data, media_type="image/jpeg")


@router.patch("/{violation_id}", response_model=ViolationResponse)
def update_violation(
    violation_id: int,
    body: ViolationUpdate,
    db: Session = Depends(get_db),
):
    violation = db.query(Violation).filter(Violation.id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    if body.plate_number is not None:
        violation.plate_number = body.plate_number
    if body.reviewed is not None:
        violation.reviewed = body.reviewed

    db.commit()
    db.refresh(violation)
    return violation


@router.delete("/{violation_id}", status_code=204)
def delete_violation(violation_id: int, db: Session = Depends(get_db)):
    violation = db.query(Violation).filter(Violation.id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    storage = get_storage()
    try:
        storage.delete(violation.evidence_image_path)
    except FileNotFoundError:
        pass

    db.delete(violation)
    db.commit()
