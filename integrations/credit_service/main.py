"""
Motor de Regras de Crédito - API Mock
Porta: 8003
Responsável por: gerar cenários de renegociação baseados em regras
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Credit Rules Service API",
    description="API mock para simular motor de regras de crédito e renegociação",
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
    return {"status": "ok", "service": "credit_service"}

# Importar router
from .routers import credit_rules

app.include_router(credit_rules.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
