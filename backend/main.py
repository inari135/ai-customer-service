"""
FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的生命周期管理"""
    # 数据库初始化：
    # 1. create_all() — 确保表存在（幂等，首次启动建表）
    # 2. 后续模型变更请使用 alembic 迁移：
    #    $ alembic revision --autogenerate -m "描述"
    #    $ alembic upgrade head
    from backend.models import init_db
    init_db()
    logger.info("数据库初始化完成")

    yield
    logger.info("服务关闭")


app = FastAPI(
    title="AI 智能客服平台",
    description="企业级 AI 客服 SaaS —— 知识库管理 + RAG 检索 + AI 对话 + 数据分析",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS：允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 全局异常处理 ---

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """兜底异常处理：避免泄漏内部错误栈"""
    logger.error(f"未处理的异常 [{request.method} {request.url.path}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"},
    )


# --- 基础路由 ---

@app.get("/")
def root():
    return {"message": "AI 智能客服平台 API", "version": "0.1.0"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# --- 注册子路由 ---
from backend.auth import router as auth_router
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
from backend.upload import router as upload_router
app.include_router(upload_router, prefix="/api/knowledge", tags=["知识库"])
from backend.rag import router as rag_router
app.include_router(rag_router, prefix="/api/rag", tags=["检索"])
from backend.agent import router as agent_router
app.include_router(agent_router, prefix="/api/chat", tags=["对话"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=settings.API_PORT, reload=True)
