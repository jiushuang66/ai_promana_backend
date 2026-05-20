import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ai_promana_backend.api.v1.routes import router as api_v1_router
from ai_promana_backend.config import settings

app = FastAPI(
    title="AI Promana Backend",
    description="AI Promana 后端 API 服务 - 用户认证系统",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)

@app.get("/", summary="健康检查", description="检查服务是否正常运行")
def health_check():
    return {"status": "ok", "service": "ai-promana-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
