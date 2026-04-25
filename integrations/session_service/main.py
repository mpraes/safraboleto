"""
Session Store - API Mock
Porta: 8005
Responsável por: armazenar estado da sessão do agente
"""
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional, List
import uuid
from pydantic import BaseModel

from integrations.shared.database import (
    get_db_session, Session, Customer, Interaction
)

app = FastAPI(
    title="Session Store API",
    description="API mock para armazenar estado de sessões do agente",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateSessionRequest(BaseModel):
    customer_id: str
    contact_id: Optional[str] = None
    channel: str = "web"
    initial_state: dict = {}


class SessionResponse(BaseModel):
    session_id: str
    customer_id: str
    contact_id: Optional[str]
    channel: str
    status: str
    state_data: dict
    created_at: str
    expires_at: Optional[str]


@app.get("/health")
async def health_check():
    """Health check do serviço"""
    return {"status": "ok", "service": "session_service"}


@app.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Cria sessão com contexto de cliente"""
    try:
        cust_uuid = uuid.UUID(request.customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID do cliente inválido")
    
    session = Session(
        customer_id=cust_uuid,
        contact_id=uuid.UUID(request.contact_id) if request.contact_id else None,
        channel=request.channel,
        status="active",
        state_data=request.initial_state,
        expires_at=datetime.utcnow() + timedelta(minutes=60)
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return SessionResponse(
        session_id=str(session.session_id),
        customer_id=str(session.customer_id),
        contact_id=str(session.contact_id) if session.contact_id else None,
        channel=session.channel,
        status=session.status,
        state_data=session.state_data or {},
        created_at=session.created_at.isoformat(),
        expires_at=session.expires_at.isoformat() if session.expires_at else None
    )


@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Recupera sessão completa"""
    try:
        sess_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID da sessão inválido")
    
    result = await db.execute(
        select(Session).where(Session.session_id == sess_uuid)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    return SessionResponse(
        session_id=str(session.session_id),
        customer_id=str(session.customer_id),
        contact_id=str(session.contact_id) if session.contact_id else None,
        channel=session.channel,
        status=session.status,
        state_data=session.state_data or {},
        created_at=session.created_at.isoformat(),
        expires_at=session.expires_at.isoformat() if session.expires_at else None
    )


@app.put("/sessions/{session_id}")
async def update_session(
    session_id: str,
    state_data: dict,
    selected_invoice_ids: Optional[List[str]] = None,
    session_constraints: Optional[dict] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Atualiza sessão"""
    try:
        sess_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID da sessão inválido")
    
    result = await db.execute(
        select(Session).where(Session.session_id == sess_uuid)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    session.state_data = state_data
    if selected_invoice_ids:
        session.selected_invoice_ids = [uuid.UUID(sid) for sid in selected_invoice_ids]
    if session_constraints:
        session.session_constraints = session_constraints
    session.last_interaction_at = datetime.utcnow()
    
    await db.commit()
    
    return {"session_id": session_id, "updated": True}


@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Remove sessão"""
    try:
        sess_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID da sessão inválido")
    
    result = await db.execute(
        select(Session).where(Session.session_id == sess_uuid)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    session.status = "expired"
    await db.commit()
    
    return {"session_id": session_id, "deleted": True}


@app.get("/sessions/customer/{customer_id}/inactive")
async def get_inactive_customers(
    customer_id: str,
    days: int = 90,
    db: AsyncSession = Depends(get_db_session)
):
    """Identifica clientes inativos para win-back"""
    try:
        cust_uuid = uuid.UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID do cliente inválido")
    
    threshold = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(Session).where(
            Session.customer_id == cust_uuid,
            Session.last_interaction_at < threshold
        )
    )
    sessions = result.scalars().all()
    
    is_inactive = len(sessions) > 0 or True
    
    return {
        "customer_id": customer_id,
        "is_inactive": is_inactive,
        "days_inactive": days,
        "last_interaction": sessions[0].last_interaction_at.isoformat() if sessions else None
    }


@app.post("/sessions/{session_id}/winback")
async def trigger_winback(
    session_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Dispara estratégia de win-back"""
    try:
        sess_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID da sessão inválido")
    
    result = await db.execute(
        select(Session).where(Session.session_id == sess_uuid)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    return {
        "session_id": session_id,
        "winback_triggered": True,
        "offer": {
            "discount_percentage": 8.0,
            "message": "Oferta especial de win-back: 8% de desconto!",
            "valid_days": 15
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
