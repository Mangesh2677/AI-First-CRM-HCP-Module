import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.agent.tools import _extract_structured_fields

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.get("/", response_model=list[schemas.InteractionOut])
def list_interactions(hcp_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Interaction)
    if hcp_id:
        query = query.filter(models.Interaction.hcp_id == hcp_id)
    return query.order_by(models.Interaction.interaction_date.desc()).all()


@router.get("/{interaction_id}", response_model=schemas.InteractionOut)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.post("/", response_model=schemas.InteractionOut)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    """Used by the structured Log Interaction form. Runs the same LLM-based
    summarization/extraction the chat agent's log_interaction tool uses, so
    both entry points produce consistent, enriched records.
    """
    hcp = db.query(models.HCP).filter(models.HCP.id == payload.hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")

    fields = _extract_structured_fields(payload.raw_notes or "")

    interaction = models.Interaction(
        hcp_id=payload.hcp_id,
        interaction_type=payload.interaction_type,
        interaction_date=payload.interaction_date or dt.datetime.utcnow(),
        raw_notes=payload.raw_notes,
        summary=fields.get("summary", ""),
        sentiment=fields.get("sentiment", "neutral"),
        products_discussed=payload.products_discussed or fields.get("products_discussed", ""),
        next_steps=payload.next_steps or fields.get("next_steps", ""),
        created_via="form",
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@router.put("/{interaction_id}", response_model=schemas.InteractionOut)
def update_interaction(interaction_id: int, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    """Used by the 'Edit Interaction' UI action on a logged record."""
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(interaction, key, value)
    interaction.updated_at = dt.datetime.utcnow()

    db.commit()
    db.refresh(interaction)
    return interaction


@router.delete("/{interaction_id}")
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    db.delete(interaction)
    db.commit()
    return {"ok": True}
