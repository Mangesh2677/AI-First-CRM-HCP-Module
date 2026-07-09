import datetime as dt

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.database import Base


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    specialty = Column(String(120), nullable=True)
    organization = Column(String(160), nullable=True)
    email = Column(String(160), nullable=True)
    phone = Column(String(40), nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False)
    interaction_type = Column(
        Enum("visit", "call", "email", "conference", name="interaction_type"),
        default="visit",
    )
    interaction_date = Column(DateTime, default=dt.datetime.utcnow)
    raw_notes = Column(Text, nullable=True)  # what the rep actually typed / said
    summary = Column(Text, nullable=True)  # LLM-generated summary
    sentiment = Column(String(30), nullable=True)  # LLM-extracted: positive/neutral/negative
    products_discussed = Column(Text, nullable=True)  # comma separated, LLM-extracted or form input
    next_steps = Column(Text, nullable=True)
    created_via = Column(String(20), default="form")  # "form" or "chat"
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")
    follow_ups = relationship("FollowUp", back_populates="interaction", cascade="all, delete-orphan")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=False)
    due_date = Column(DateTime, nullable=True)
    note = Column(Text, nullable=True)
    status = Column(Enum("open", "done", name="follow_up_status"), default="open")
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    interaction = relationship("Interaction", back_populates="follow_ups")
