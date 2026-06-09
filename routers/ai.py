from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def ai_health():
    return {"status": "ok", "module": "AI Pipeline"}