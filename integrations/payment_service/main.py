"""
Serviço de Pagamentos - API Mock
Porta: 8002
Responsável por: geração de boletos e PIX
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Payment Service API",
    description="API mock para simular geração de boletos e PIX",
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
    return {"status": "ok", "service": "payment_service"}


from integrations.payment_service.routers import payments

app.include_router(payments.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
