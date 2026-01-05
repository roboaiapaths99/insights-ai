from fastapi import APIRouter, Depends
from auth.dependencies import require_role

router = APIRouter(prefix="/parent", tags=["Parent Dashboard"])

@router.get("/ping")
def ping(
    user=Depends(require_role(["Parent", "Admin"])),
):
    return {"ok": True}
