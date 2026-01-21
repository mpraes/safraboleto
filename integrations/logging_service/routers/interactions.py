"""
Router para endpoints de logging de interações
"""
from fastapi import APIRouter, HTTPException
from ..models import LogInteractionRequest, LogResponse, InteractionHistory

router = APIRouter(prefix="/interactions", tags=["interactions"])

# TODO: Implementar endpoints
# POST /interactions/log
# GET /interactions/{customer_id}/history

@router.post("/log", response_model=LogResponse)
async def log_interaction(request: LogInteractionRequest):
    """Registra evento de interação"""
    raise HTTPException(status_code=501, detail="Não implementado ainda")

@router.get("/{customer_id}/history", response_model=InteractionHistory)
async def get_interaction_history(customer_id: str):
    """Consulta histórico de interações de um cliente"""
    raise HTTPException(status_code=501, detail="Não implementado ainda")
