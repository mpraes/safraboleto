"""
Modelos Pydantic para o serviço de logging
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class LogInteractionRequest(BaseModel):
    session_id: str
    customer_id: str
    event_type: str  # proposal_presented, proposal_accepted, proposal_rejected, escalation, agreement_created
    event_data: dict
    timestamp: Optional[str] = None

class LogResponse(BaseModel):
    log_id: str
    status: str

class InteractionHistoryItem(BaseModel):
    log_id: str
    session_id: str
    event_type: str
    event_data: dict
    timestamp: str

class InteractionHistory(BaseModel):
    customer_id: str
    interactions: List[InteractionHistoryItem]
    total_count: int
