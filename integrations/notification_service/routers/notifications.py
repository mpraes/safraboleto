"""
Router para endpoints de notificações
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional, List
import uuid
from pydantic import BaseModel

from integrations.shared.database import (
    get_db_session, Notification, NotificationChannel, NotificationStatus
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


class Recipient(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None


class Attachment(BaseModel):
    type: str
    url: str


class SendNotificationRequest(BaseModel):
    channel: str
    recipient: Recipient
    template: str
    variables: dict
    attachments: Optional[List[Attachment]] = None


class NotificationResponse(BaseModel):
    notification_id: str
    status: str
    channel: str
    sent_at: str
    message_id: Optional[str] = None


class NotificationStatusResponse(BaseModel):
    notification_id: str
    status: str
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None


TEMPLATE_MESSAGES = {
    "agreement_confirmation": "Olá {name}, seu acordo foi confirmado! Valor total: R$ {total_amount}.",
    "invoice_reminder": "Olá {name}, você tem faturas em aberto no valor de R$ {total_amount}.",
    "payment_link": "Olá {name}, acesse o link para pagamento: {payment_url}",
    "winback_offer": "Olá {name}, temos uma oferta especial para você regularizar sua situação. Desconto de {discount}%!"
}


@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    request: SendNotificationRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Envia notificação por canal"""
    try:
        channel = NotificationChannel(request.channel)
    except ValueError:
        raise HTTPException(status_code=400, detail="Canal de notificação inválido")
    
    notification = Notification(
        channel=channel,
        template=request.template,
        recipient_name=request.recipient.name,
        recipient_phone=request.recipient.phone,
        recipient_email=request.recipient.email,
        variables=request.variables,
        attachments=[a.model_dump() for a in request.attachments] if request.attachments else [],
        status=NotificationStatus.sent,
        message_id=f"MSG-{uuid.uuid4().hex[:8].upper()}",
        sent_at=datetime.utcnow()
    )
    
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    
    return NotificationResponse(
        notification_id=str(notification.notification_id),
        status=notification.status.value,
        channel=notification.channel.value,
        sent_at=notification.sent_at.isoformat(),
        message_id=notification.message_id
    )


@router.get("/{notification_id}/status", response_model=NotificationStatusResponse)
async def get_notification_status(
    notification_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Consulta status de uma notificação"""
    try:
        notif_uuid = uuid.UUID(notification_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID da notificação inválido")
    
    result = await db.execute(
        select(Notification).where(Notification.notification_id == notif_uuid)
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    
    return NotificationStatusResponse(
        notification_id=str(notification.notification_id),
        status=notification.status.value,
        delivered_at=notification.delivered_at.isoformat() if notification.delivered_at else None,
        read_at=notification.read_at.isoformat() if notification.read_at else None
    )


@router.get("/templates")
async def list_templates():
    """Lista templates disponíveis por canal"""
    return {
        "templates": [
            {
                "name": name,
                "message": message,
                "channels": ["whatsapp", "sms", "email"]
            }
            for name, message in TEMPLATE_MESSAGES.items()
        ]
    }
