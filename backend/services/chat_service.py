"""
对话服务：Prompt 构建 + LLM 调用 + 置信度解析 + 对话编排
从 agent.py 的路由处理中分离出来，方便测试和复用
"""
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.config import settings
from backend.models import Company, Conversation, Message
from backend.rag import search_knowledge_base


def build_prompt(
    query: str,
    sources: list[dict],
    history: list[dict],
    company: Company,
) -> str:
    """构建发给 LLM 的完整 Prompt"""
    # 知识库内容
    knowledge = ""
    if sources:
        knowledge_parts = []
        for i, s in enumerate(sources, 1):
            knowledge_parts.append(f"[资料{i}] {s['content']}")
        knowledge = "\n".join(knowledge_parts)
    else:
        knowledge = "（知识库中没有找到相关信息）"

    # 对话历史（最近 5 轮）
    history_text = ""
    if history:
        recent = history[-10:]  # 最近 10 条消息（5 轮对话）
        for msg in recent:
            role_name = "用户" if msg["role"] == "user" else "客服"
            history_text += f"{role_name}: {msg['content']}\n"

    tone_map = {
        "professional": "专业、礼貌",
        "friendly": "亲切、热情",
        "concise": "简洁、高效",
    }
    tone_desc = tone_map.get(company.ai_tone, "专业、礼貌")

    prompt = f"""你是一个{tone_desc}的AI客服助手，代表"{company.name}"回答用户问题。

## 知识库参考资料
{knowledge}

## 对话历史
{history_text if history_text else "（新对话）"}

## 当前用户问题
{query}

## 回答要求
1. 优先基于知识库资料回答，不要编造信息
2. 如果知识库没有相关信息，礼貌告知用户并建议联系人工客服
3. 回答语气为：{tone_desc}
4. 回复最后一行请以JSON格式输出置信度评估（仅用于系统判断，用户不可见）：
{{"confidence": "high/medium/low", "reason": "简短说明"}}

请回答："""

    return prompt


def parse_response(response: str) -> tuple[str, str]:
    """从 LLM 回复中分离正文和置信度 JSON"""
    lines = response.strip().split("\n")
    confidence = "medium"
    reply = response

    # 从最后几行中找 JSON
    for i in range(len(lines) - 1, max(len(lines) - 5, -1), -1):
        line = lines[i].strip()
        if line.startswith("{") and "confidence" in line:
            try:
                data = json.loads(line)
                confidence = data.get("confidence", "medium")
                reply = "\n".join(lines[:i]).strip()
                break
            except json.JSONDecodeError:
                continue

    return reply, confidence


def call_llm(prompt: str) -> str:
    """调用 LLM API 生成回复"""
    provider = settings.LLM_PROVIDER

    if provider == "deepseek":
        return _call_deepseek(prompt)
    elif provider == "openai":
        return _call_openai(prompt)
    elif provider == "anthropic":
        return _call_anthropic(prompt)
    else:
        raise ValueError(f"不支持的 LLM 提供商：{provider}")


def _call_deepseek(prompt: str) -> str:
    """调用 DeepSeek API（OpenAI 兼容格式）"""
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
    )
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def _call_openai(prompt: str) -> str:
    """调用 OpenAI API"""
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def _call_anthropic(prompt: str) -> str:
    """调用 Anthropic Claude API"""
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def chat(
    company: Company,
    user_message: str,
    conversation_id: int | None,
    db: Session,
) -> dict:
    """核心对话逻辑：检索 → 生成 → 保存 → 返回"""

    # 1. 获取或创建对话
    if conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.company_id == company.id,
        ).first()
        if not conv:
            raise HTTPException(status_code=404, detail="对话不存在")
    else:
        conv = Conversation(company_id=company.id)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # 2. 获取对话历史
    history_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in history_messages]

    # 3. 保存用户消息
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=user_message,
    )
    db.add(user_msg)
    db.commit()

    # 4. RAG 检索
    sources = search_knowledge_base(company.id, user_message)

    # 5. 构建 Prompt + 调用 LLM
    prompt = build_prompt(user_message, sources, history, company)
    raw_response = call_llm(prompt)
    reply, confidence = parse_response(raw_response)

    # 6. 保存 AI 回复
    ai_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=reply,
        confidence=confidence,
        sources=json.dumps(sources, ensure_ascii=False) if sources else None,
    )
    db.add(ai_msg)
    db.commit()

    return {
        "conversation_id": conv.id,
        "reply": reply,
        "confidence": confidence,
        "sources": sources,
    }
