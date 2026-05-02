from fastapi import APIRouter, Depends

from app.api.deps import get_store
from app.api.response import ok
from app.services.store import DemoStore

router = APIRouter(prefix="/api/context", tags=["context"])


@router.get("/me")
def get_demo_me(demo_store: DemoStore = Depends(get_store)) -> dict:
    return ok(demo_store.get_seed_context())


@router.get("/seed")
def get_seed_context(demo_store: DemoStore = Depends(get_store)) -> dict:
    return ok(demo_store.get_seed_context())
