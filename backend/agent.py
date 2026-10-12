"""
AI 对话 Agent：路由层（业务逻辑在 services/chat_service.py）
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models import Company, Conversation, get_db
from backend.schemas import ChatRequest, ChatResponse, ConversationItem, MessageItem
from backend.auth import get_current_company
from backend.services.chat_service import chat

router = APIRouter()


# --- API 路由 ---

@router.post("/send", response_model=ChatResponse)
def send_message(
    req: ChatRequest,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """发送消息给 AI 客服"""
    result = chat(
        company=company,
        user_message=req.message,
        conversation_id=req.conversation_id,
        db=db,
    )
    return ChatResponse(**result)


@router.get("/conversations", response_model=list[ConversationItem])
def list_conversations(
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """获取对话列表"""
    convs = (
        db.query(Conversation)
        .filter(Conversation.company_id == company.id)
        .order_by(Conversation.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": c.id,
            "visitor_name": c.visitor_name,
            "status": c.status,
            "satisfaction": c.satisfaction,
            "message_count": len(c.messages),
            "created_at": c.created_at.isoformat(),
        }
        for c in convs
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageItem])
def get_messages(
    conversation_id: int,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """获取某对话的消息历史"""
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.company_id == company.id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "confidence": m.confidence,
            "created_at": m.created_at.isoformat(),
        }
        for m in conv.messages
    ]
