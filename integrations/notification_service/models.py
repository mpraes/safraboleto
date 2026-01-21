"""
Modelos Pydantic para o serviço de notificações
"""
from pydantic import BaseModel
from typing import Optional, List

class Recipient(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None

class Attachment(BaseModel):
    type: str  # pdf, image, etc
    url: str

class SendNotificationRequest(BaseModel):
    channel: str  # whatsapp, sms, email
    recipient: Recipient
    template: str  # agreement_confirmation, invoice_reminder, payment_link
    variables: dict
    attachments: Optional[List[Attachment]] = None

class NotificationResponse(BaseModel):
    notification_id: str
    status: str  # sent, failed, pending
    channel: str
    sent_at: str
    message_id: Optional[str] = None

class NotificationStatus(BaseModel):
    notification_id: str
    status: str  # sent, delivered, read, failed
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None
