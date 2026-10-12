"""
SQLite 数据模型：企业、用户、文档、对话、消息
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone

from backend.config import settings

# 确保数据库目录存在
db_dir = os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", ""))
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 需要
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)


# --- 数据模型 ---

class Company(Base):
    """企业/租户"""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="企业名称")
    email = Column(String(200), unique=True, nullable=False, comment="企业邮箱")
    password_hash = Column(String(200), nullable=False, comment="密码哈希")
    welcome_message = Column(String(500), default="您好，我是AI客服助手，请问有什么可以帮您？")
    ai_tone = Column(String(100), default="professional", comment="AI语气：professional/friendly/concise")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    documents = relationship("Document", back_populates="company")
    conversations = relationship("Conversation", back_populates="company")


class Document(Base):
    """知识库文档"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    filename = Column(String(500), nullable=False, comment="原始文件名")
    file_type = Column(String(20), nullable=False, comment="txt/pdf/docx")
    content = Column(Text, nullable=False, comment="文档纯文本内容")
    chunk_count = Column(Integer, default=0, comment="分块数量")
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="documents")


class Conversation(Base):
    """对话会话"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    visitor_name = Column(String(100), default="匿名用户")
    status = Column(String(20), default="active", comment="active/closed/transferred")
    satisfaction = Column(Integer, nullable=True, comment="用户满意度 1-5")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")


class Message(Base):
    """对话消息"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False, comment="user/assistant/system")
    content = Column(Text, nullable=False)
    confidence = Column(String(20), nullable=True, comment="high/medium/low（仅AI消息）")
    sources = Column(Text, nullable=True, comment="引用的知识库片段（JSON）")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")


class ChunkVector(Base):
    """文档分块 + 向量数组（与业务表同一数据库）"""
    __tablename__ = "chunk_vectors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False, comment="分块序号")
    content = Column(Text, nullable=False, comment="分块文本")
    embedding = Column(Text, nullable=False, comment="向量（JSON 数组字符串）")
    token_count = Column(Integer, default=0, comment="分块 token 数（估算）")
