from fastapi import FastAPI
from routers import ai

app = FastAPI(
    title="See-Nears AI Pipeline",
    description="어르신 음성 감정분석 API",
    version="0.1.0"
)

app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI 분석"])

@app.get("/")
def health_check():
    return {"status": "ok", "service": "See-Nears AI Pipeline"}