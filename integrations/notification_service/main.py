"""
Serviço de Notificações - API Mock
Porta: 8004
Responsável por: simular envio de mensagens
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Notification Service API",
    description="API mock para simular envio de notificações",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check do serviço"""
    return {"status": "ok", "service": "notification_service"}


from integrations.notification_service.routers import notifications

app.include_router(notifications.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
