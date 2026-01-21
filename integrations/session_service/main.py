"""
Session Store - API Mock
Porta: 8005
Responsável por: armazenar estado da sessão do agente
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/health")
async def health_check():
    """Health check do serviço"""
    return {"status": "ok", "service": "session_service"}

# TODO: Implementar endpoints de sessão
# POST /sessions
# GET /sessions/{session_id}
# PUT /sessions/{session_id}
# DELETE /sessions/{session_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
