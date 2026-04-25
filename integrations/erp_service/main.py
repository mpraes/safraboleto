"""
Serviço ERP Financeiro - API Mock
Porta: 8001
Responsável por: clientes, faturas e acordos
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ERP Financeiro API",
    description="API mock para simular sistema ERP de contas a receber",
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
    return {"status": "ok", "service": "erp_service"}


from integrations.erp_service.routers import customers, invoices, agreements

app.include_router(customers.router)
app.include_router(invoices.router)
app.include_router(agreements.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
