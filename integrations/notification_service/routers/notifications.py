"""
Router para endpoints de notificações
"""
from fastapi import APIRouter, HTTPException
from ..models import SendNotificationRequest, NotificationResponse, NotificationStatus

router = APIRouter(prefix="/notifications", tags=["notifications"])

# TODO: Implementar endpoints
# POST /notifications/send
# GET /notifications/{notification_id}/status

@router.post("/send", response_model=NotificationResponse)
async def send_notification(request: SendNotificationRequest):
    """Envia notificação por canal"""
    raise HTTPException(status_code=501, detail="Não implementado ainda")

@router.get("/{notification_id}/status", response_model=NotificationStatus)
async def get_notification_status(notification_id: str):
    """Consulta status de uma notificação"""
    raise HTTPException(status_code=501, detail="Não implementado ainda")
