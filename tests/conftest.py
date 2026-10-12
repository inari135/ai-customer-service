"""
测试基础设施：临时数据库 + FastAPI TestClient
"""
import os
import tempfile
import atexit

# === 必须在导入任何 backend 模块之前设置环境变量 ===
# load_dotenv() 不会覆盖已有的 os.environ，所以这里设置是安全的

_db_fd, _db_path = tempfile.mkstemp(suffix=".db", prefix="test_ai_cs_")
os.close(_db_fd)

os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRE_MINUTES"] = "60"
os.environ["SILICONFLOW_API_KEY"] = "test-sk-siliconflow"
os.environ["DEEPSEEK_API_KEY"] = "test-sk-deepseek"
os.environ["LLM_PROVIDER"] = "deepseek"
os.environ["EMBEDDING_PROVIDER"] = "siliconflow"


def _cleanup_temp_db():
    """清理临时数据库文件"""
    try:
        if os.path.exists(_db_path):
            os.unlink(_db_path)
    except OSError:
        pass


atexit.register(_cleanup_temp_db)

# === 现在可以安全导入 backend 模块 ===

import pytest
from fastapi.testclient import TestClient

from backend.models import Base, engine, SessionLocal
from backend.main import app


@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前重建所有表，保证测试隔离"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db():
    """数据库会话"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def client():
    """FastAPI 测试客户端（模块级复用，避免重复触发 lifespan）"""
    with TestClient(app) as c:
        yield c
