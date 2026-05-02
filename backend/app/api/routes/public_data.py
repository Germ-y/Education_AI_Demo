from fastapi import APIRouter, Depends

from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/public-data", tags=["public-data"])


@router.get("/sources")
def list_sources(_: SessionPrincipal = Depends(require_teacher), demo_store: DemoStore = Depends(get_store)) -> dict:
    return ok([source.model_dump(by_alias=True) for source in demo_store.db.public_data_sources])
