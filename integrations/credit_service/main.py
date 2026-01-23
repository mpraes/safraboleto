"""
Motor de Regras de Crédito - API Mock
Porta: 8003
Responsável por: gerar cenários de renegociação baseados em regras
"""
import sys
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path para permitir imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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
from integrations.credit_service.routers import credit_rules

app.include_router(credit_rules.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
