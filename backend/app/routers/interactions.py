from fastapi import APIRouter

from backend.app.api_models import InteractionRequest, InteractionResult
from backend.app.services.interactions import check_interactions

router = APIRouter()


@router.post("/interactions", response_model=InteractionResult)
def post_interactions(body: InteractionRequest) -> InteractionResult:
    return InteractionResult(**check_interactions(body.rxcuis))
