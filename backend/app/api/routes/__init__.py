from fastapi import APIRouter

from app.api.routes.documents import router as documents_router
from app.api.routes.kbs import router as kbs_router
from app.api.routes.query import router as query_router

router = APIRouter()
router.include_router(kbs_router, prefix="/kbs", tags=["kbs"])
router.include_router(documents_router, prefix="/kbs", tags=["documents"])
router.include_router(query_router, prefix="/kbs", tags=["rag"])


