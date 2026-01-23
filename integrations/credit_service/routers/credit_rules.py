"""
Router para endpoints de regras de crédito
"""
from fastapi import APIRouter, HTTPException
from integrations.credit_service.models import GenerateOptionsRequest, GenerateOptionsResponse, ValidateScenarioRequest, ValidateScenarioResponse

router = APIRouter(prefix="/credit-rules", tags=["credit-rules"])

# TODO: Implementar endpoints
# POST /credit-rules/generate-options
# POST /credit-rules/validate-scenario

@router.post("/generate-options", response_model=GenerateOptionsResponse)
async def generate_options(request: GenerateOptionsRequest):
    """Gera cenários de renegociação baseados em regras de crédito"""
    raise HTTPException(status_code=501, detail="Não implementado ainda")

@router.post("/validate-scenario", response_model=ValidateScenarioResponse)
async def validate_scenario(request: ValidateScenarioRequest):
    """Valida se um cenário escolhido ainda está dentro das regras"""
    raise HTTPException(status_code=501, detail="Não implementado ainda")
