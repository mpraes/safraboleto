"""
Router para endpoints de acordos de renegociação
"""
from fastapi import APIRouter, HTTPException
from integrations.erp_service.models import CreateAgreementRequest, Agreement

router = APIRouter(prefix="/agreements", tags=["agreements"])

# TODO: Implementar endpoints
# POST /agreements
# GET /agreements/{agreement_id}

@router.post("", response_model=Agreement)
async def create_agreement(request: CreateAgreementRequest):
    """Cria um novo acordo de renegociação"""
    # TODO: Validar dados, criar acordo, retornar
    raise HTTPException(status_code=501, detail="Não implementado ainda")

@router.get("/{agreement_id}", response_model=Agreement)
async def get_agreement(agreement_id: str):
    """Consulta status de um acordo"""
    # TODO: Buscar acordo e retornar
    raise HTTPException(status_code=501, detail="Não implementado ainda")
