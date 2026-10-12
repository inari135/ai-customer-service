"""
Pydantic 请求/响应模型
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# --- 认证 ---

class CompanyRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, description="企业名称")
    email: EmailStr = Field(..., description="企业邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="密码（6-100位）")


class CompanyLogin(BaseModel):
    email: EmailStr = Field(..., description="企业邮箱")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    company_id: int
    company_name: str


class CompanyInfo(BaseModel):
    """企业信息（/me 接口返回）"""
    id: int
    name: str
    email: str
    welcome_message: Optional[str] = None
    ai_tone: Optional[str] = None


# --- 知识库 ---

class DocumentInfo(BaseModel):
    id: int
    filename: str
    file_type: str
    chunk_count: int
    uploaded_at: str


class UploadResponse(BaseModel):
    message: str
    document: DocumentInfo


# --- 检索 ---

class SearchResultItem(BaseModel):
    chunk_id: int
    document_id: int
    content: str
    score: float


class SearchResponse(BaseModel):
    query: str
    total_chunks: int
    results: list[SearchResultItem]


class StatsResponse(BaseModel):
    document_count: int
    chunk_count: int


# --- 对话 ---

class ChatRequest(BaseModel):
    company_id: int
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[int] = None  # None 则创建新对话


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    confidence: str  # high/medium/low
    sources: Optional[list[dict]] = None


class ConversationItem(BaseModel):
    id: int
    visitor_name: str
    status: str
    satisfaction: Optional[int] = None
    message_count: int
    created_at: str


class MessageItem(BaseModel):
    id: int
    role: str
    content: str
    confidence: Optional[str] = None
    created_at: str


# --- 通用 ---

class MessageResponse(BaseModel):
    message: str
