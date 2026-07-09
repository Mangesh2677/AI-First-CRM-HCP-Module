import datetime as dt
from typing import Optional, List

from pydantic import BaseModel


class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    organization: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class HCPCreate(HCPBase):
    pass


class HCPOut(HCPBase):
    id: int

    class Config:
        from_attributes = True


class InteractionBase(BaseModel):
    hcp_id: int
    interaction_type: str = "visit"
    interaction_date: Optional[dt.datetime] = None
    raw_notes: Optional[str] = None
    products_discussed: Optional[str] = None
    next_steps: Optional[str] = None


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    interaction_date: Optional[dt.datetime] = None
    raw_notes: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    products_discussed: Optional[str] = None
    next_steps: Optional[str] = None


class InteractionOut(BaseModel):
    id: int
    hcp_id: int
    interaction_type: str
    interaction_date: dt.datetime
    raw_notes: Optional[str]
    summary: Optional[str]
    sentiment: Optional[str]
    products_discussed: Optional[str]
    next_steps: Optional[str]
    created_via: str
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatToolCall(BaseModel):
    tool: str
    output: str


class ChatResponse(BaseModel):
    reply: str
    tool_calls: List[ChatToolCall] = []
