"""
Router para endpoints de logging de interações
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Optional, List
import uuid
from pydantic import BaseModel

from integrations.shared.database import (
    get_db_session, Interaction, InteractionEventType
)

router = APIRouter(prefix="/interactions", tags=["interactions"])


class LogInteractionRequest(BaseModel):
    session_id: str
    customer_id: str
    event_type: str
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


@router.post("/log", response_model=LogResponse)
async def log_interaction(
    request: LogInteractionRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Registra evento de interação"""
    try:
        sess_uuid = uuid.UUID(request.session_id)
        cust_uuid = uuid.UUID(request.customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="IDs inválidos")
    
    try:
        event_type = InteractionEventType(request.event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Tipo de evento inválido")
    
    interaction = Interaction(
        session_id=sess_uuid,
        customer_id=cust_uuid,
        event_type=event_type,
        event_data=request.event_data,
        created_at=datetime.fromisoformat(request.timestamp) if request.timestamp else datetime.utcnow()
    )
    
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    
    return LogResponse(
        log_id=str(interaction.interaction_id),
        status="logged"
    )


@router.get("/{customer_id}/history", response_model=InteractionHistory)
async def get_interaction_history(
    customer_id: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session)
):
    """Consulta histórico de interações de um cliente"""
    try:
        cust_uuid = uuid.UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID do cliente inválido")
    
    count_result = await db.execute(
        select(func.count()).where(Interaction.customer_id == cust_uuid)
    )
    total_count = count_result.scalar() or 0
    
    result = await db.execute(
        select(Interaction)
        .where(Interaction.customer_id == cust_uuid)
        .order_by(Interaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    interactions = result.scalars().all()
    
    return InteractionHistory(
        customer_id=customer_id,
        interactions=[
            InteractionHistoryItem(
                log_id=str(i.interaction_id),
                session_id=str(i.session_id),
                event_type=i.event_type.value,
                event_data=i.event_data or {},
                timestamp=i.created_at.isoformat()
            )
            for i in interactions
        ],
        total_count=total_count
    )


@router.get("/analytics")
async def get_analytics(
    days: int = 30,
    db: AsyncSession = Depends(get_db_session)
):
    """Métricas agregadas de interações"""
    from datetime import timedelta
    
    threshold = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(
            Interaction.event_type,
            func.count(Interaction.interaction_id).label("count")
        )
        .where(Interaction.created_at >= threshold)
        .group_by(Interaction.event_type)
    )
    
    event_counts = {row.event_type.value: row.count for row in result}
    
    return {
        "period_days": days,
        "total_interactions": sum(event_counts.values()),
        "by_event_type": event_counts
    }
