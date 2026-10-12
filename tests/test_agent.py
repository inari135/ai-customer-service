"""
测试对话服务：Prompt 构建、响应解析、对话编排
"""
from unittest.mock import patch

import pytest
from fastapi import status

from backend.services.chat_service import build_prompt, parse_response, chat
from backend.models import Company


# ============================================================
# 纯函数测试：Prompt 构建
# ============================================================

class TestBuildPrompt:
    """build_prompt()"""

    @pytest.fixture
    def company(self):
        return Company(
            id=1,
            name="测试科技公司",
            email="test@tech.com",
            password_hash="xxx",
            ai_tone="professional",
            welcome_message="您好，我是AI客服",
        )

    def test_builds_prompt_with_sources(self, company):
        """有知识库资料 → Prompt 包含资料内容"""
        sources = [
            {"chunk_id": 1, "content": "我们的退款政策是 7 天无理由退款", "score": 0.9},
        ]
        prompt = build_prompt("如何退款？", sources, [], company)

        assert "测试科技公司" in prompt
        assert "7 天无理由退款" in prompt
        assert "如何退款？" in prompt
        assert "专业" in prompt  # professional tone

    def test_builds_prompt_without_sources(self, company):
        """无知识库资料 → Prompt 包含占位提示"""
        prompt = build_prompt("复杂问题", [], [], company)

        assert "知识库中没有找到相关信息" in prompt
        assert "复杂问题" in prompt

    def test_builds_prompt_with_history(self, company):
        """有对话历史 → Prompt 包含历史记录"""
        history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "您好！有什么可以帮助您的？"},
        ]
        prompt = build_prompt("退款", [], history, company)

        assert "你好" in prompt
        assert "退款" in prompt

    def test_builds_prompt_truncates_long_history(self, company):
        """历史超过 10 条 → 只取最近 10 条"""
        history = [{"role": "user", "content": f"消息{i}"} for i in range(20)]
        prompt = build_prompt("当前问题", [], history, company)

        # 前 10 条不应该出现，"消息0" ~ "消息9" 不在 prompt 中
        assert "消息0" not in prompt
        # 但最近 10 条会出现
        assert "消息19" in prompt

    def test_builds_prompt_with_friendly_tone(self, company):
        """ai_tone=friendly → Prompt 包含亲切语气描述"""
        company.ai_tone = "friendly"
        prompt = build_prompt("问题", [], [], company)
        assert "亲切" in prompt

    def test_builds_prompt_with_concise_tone(self, company):
        """ai_tone=concise → Prompt 包含简洁语气描述"""
        company.ai_tone = "concise"
        prompt = build_prompt("问题", [], [], company)
        assert "简洁" in prompt


# ============================================================
# 纯函数测试：响应解析
# ============================================================

class TestParseResponse:
    """parse_response()"""

    def test_extracts_confidence_json_last_line(self):
        """最后一行为合法 JSON → 正确分离正文和置信度"""
        response = """这是对您问题的回答。
根据查询结果，退款政策是7天无理由退款。
{"confidence": "high", "reason": "知识库有明确的退款政策"}"""

        reply, confidence = parse_response(response)

        assert "7天无理由退款" in reply
        assert "退款政策" in reply
        # 正文不应包含 JSON
        assert "confidence" not in reply
        assert confidence == "high"

    def test_returns_default_confidence_on_no_json(self):
        """响应中无 JSON → 返回原文本 + 默认 medium"""
        response = "这只是一段普通文本回答，没有置信度。"

        reply, confidence = parse_response(response)

        assert reply == response
        assert confidence == "medium"

    def test_finds_json_in_last_few_lines(self):
        """JSON 在倒数第 2 行 → 正确分离，JSON 之后的内容被丢弃"""
        response = """回答内容第一行。
回答内容第二行。
{"confidence": "low", "reason": "知识库信息不足"}
（注：仅供参考）"""

        reply, confidence = parse_response(response)

        # parse_response 取 lines[:i]，JSON 行之后的内容会被丢弃
        assert "回答内容第一行" in reply
        assert "回答内容第二行" in reply
        assert "仅供参考" not in reply  # JSON 行之后的内容不保留
        assert confidence == "low"

    def test_handles_invalid_json_in_last_lines(self):
        """最后几行有类似 JSON 但不是合法 JSON → 不误解析"""
        response = """回答内容。
{这不是合法的json}
{"confidence": "medium", "reason": "ok"}"""

        reply, confidence = parse_response(response)

        # 第二行的无效 JSON 被跳过，第三行合法 JSON 被识别
        assert confidence == "medium"
        assert "回答内容" in reply


# ============================================================
# chat() 函数测试：核心对话编排
# ============================================================

class TestChat:
    """chat() — 需要 mock RAG + LLM"""

    @pytest.fixture
    def company(self, db):
        """在数据库中有记录的企业"""
        c = Company(
            name="对话测试企业",
            email="chat@test.com",
            password_hash="xxx",
            ai_tone="professional",
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        return c

    def test_chat_new_conversation(self, db, company):
        """新对话（无 conversation_id）→ 创建会话 + 返回回复"""
        with patch("backend.services.chat_service.search_knowledge_base") as mock_rag:
            mock_rag.return_value = [
                {"chunk_id": 1, "content": "知识库片段", "score": 0.8},
            ]
            with patch("backend.services.chat_service.call_llm") as mock_llm:
                mock_llm.return_value = (
                    "您好！根据我们的政策，您可以申请退款。\n"
                    '{"confidence": "high", "reason": "政策明确"}'
                )

                result = chat(
                    company=company,
                    user_message="如何退款？",
                    conversation_id=None,
                    db=db,
                )

        assert result["conversation_id"] > 0
        assert "退款" in result["reply"]
        assert result["confidence"] == "high"
        assert len(result["sources"]) == 1

    def test_chat_existing_conversation(self, db, company):
        """继续已有对话 → 保存消息到同一会话"""
        # 第一次对话
        with patch("backend.services.chat_service.search_knowledge_base") as mock_rag:
            mock_rag.return_value = []
            with patch("backend.services.chat_service.call_llm") as mock_llm:
                mock_llm.return_value = "第一次回复\n" '{"confidence": "medium", "reason": "ok"}'
                r1 = chat(company, "第一个问题", None, db)

        # 第二次对话（继续）
        with patch("backend.services.chat_service.search_knowledge_base") as mock_rag:
            mock_rag.return_value = []
            with patch("backend.services.chat_service.call_llm") as mock_llm:
                mock_llm.return_value = "第二次回复\n" '{"confidence": "medium", "reason": "ok"}'
                r2 = chat(company, "第二个问题", r1["conversation_id"], db)

        assert r2["conversation_id"] == r1["conversation_id"]

        # 验证有 4 条消息（2 用户 + 2 AI）
        from backend.models import Message
        msg_count = db.query(Message).filter(
            Message.conversation_id == r1["conversation_id"]
        ).count()
        assert msg_count == 4

    def test_chat_nonexistent_conversation(self, db, company):
        """对话 ID 不存在 → 抛 404"""
        with pytest.raises(Exception) as exc:
            chat(company, "问题", conversation_id=99999, db=db)
        assert exc.value.status_code == 404

    def test_chat_preserves_message_order(self, db, company):
        """消息按 user → assistant 顺序保存"""
        with patch("backend.services.chat_service.search_knowledge_base") as mock_rag:
            mock_rag.return_value = []
            with patch("backend.services.chat_service.call_llm") as mock_llm:
                mock_llm.return_value = "AI回复\n" '{"confidence": "medium", "reason": "ok"}'
                chat(company, "用户问题", None, db)

        from backend.models import Message, Conversation
        conv = db.query(Conversation).order_by(Conversation.id.desc()).first()
        msgs = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at).all()

        assert msgs[0].role == "user"
        assert msgs[1].role == "assistant"
        assert msgs[1].confidence == "medium"


# ============================================================
# API 端点测试
# ============================================================

class TestChatAPI:
    """POST /api/chat/send"""

    def test_send_message_requires_auth(self, client):
        """无 token → 403/401"""
        resp = client.post("/api/chat/send", json={
            "company_id": 1, "message": "你好",
        })
        assert resp.status_code in (403, 401)

    def test_send_message_success(self, client):
        """有 token → 正常返回"""
        # 注册
        reg = client.post("/api/auth/register", json={
            "name": "对话API测试", "email": "chatapi@test.com", "password": "123456",
        })
        token = reg.json()["access_token"]
        company_id = reg.json()["company_id"]

        with patch("backend.services.chat_service.search_knowledge_base") as mock_rag:
            mock_rag.return_value = []
            with patch("backend.services.chat_service.call_llm") as mock_llm:
                mock_llm.return_value = "这是AI客服的回复。\n" '{"confidence": "medium", "reason": "ok"}'
                resp = client.post("/api/chat/send", json={
                    "company_id": company_id, "message": "你好",
                }, headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["conversation_id"] > 0
        assert len(data["reply"]) > 0
        assert data["confidence"] in ("high", "medium", "low")
