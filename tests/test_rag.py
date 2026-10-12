"""
测试 rag.py：语义检索（mock embedding API）
"""
import json
from unittest.mock import patch

from backend.rag import search_knowledge_base
from backend.models import ChunkVector


# 生成 1024 维的模拟向量（BGE-Large 输出维度）
def _fake_vector():
    return [0.1] * 1024


class TestSearchKnowledgeBase:
    """search_knowledge_base() 核心检索逻辑"""

    def test_returns_empty_when_no_chunks(self, db):
        """知识库为空 → 返回空列表"""
        with patch("backend.rag.get_embedding") as mock_embed:
            mock_embed.return_value = [_fake_vector()]
            results = search_knowledge_base(company_id=999, query="测试问题")
        assert results == []

    def test_returns_matching_chunks(self, db):
        """有匹配内容 → 返回排序后的结果"""
        # 1. 先在数据库中添加分块
        chunks_data = [
            ("Python 是一种编程语言", "python related"),
            ("Java 是另一种编程语言", "java related"),
            ("机器学习使用 Python", "ml related"),
        ]
        for i, (content, _) in enumerate(chunks_data):
            vec = [0.1] * 1024
            vec[i] = 0.9  # 让每个向量略有不同
            chunk = ChunkVector(
                document_id=1,
                company_id=1,
                chunk_index=i,
                content=content,
                embedding=json.dumps(vec),
                token_count=len(content),
            )
            db.add(chunk)
        db.commit()

        # 2. Mock embedding: 返回与 "Python" 相关的向量
        query_vec = [0.9, 0.1, 0.1] + [0.1] * 1021
        with patch("backend.rag.get_embedding") as mock_embed:
            mock_embed.return_value = [query_vec]
            results = search_knowledge_base(company_id=1, query="Python")

        # 3. 验证：至少有一条结果，第一条应该最相关
        assert len(results) >= 1
        assert results[0]["score"] > 0
        assert "content" in results[0]
        assert "chunk_id" in results[0]

    def test_respects_top_k(self, db):
        """top_k 参数生效"""
        # 添加 5 个分块
        for i in range(5):
            chunk = ChunkVector(
                document_id=1,
                company_id=2,
                chunk_index=i,
                content=f"内容 {i}",
                embedding=json.dumps(_fake_vector()),
                token_count=10,
            )
            db.add(chunk)
        db.commit()

        with patch("backend.rag.get_embedding") as mock_embed:
            mock_embed.return_value = [_fake_vector()]
            results = search_knowledge_base(company_id=2, query="任意问题", top_k=2)

        assert len(results) <= 2

    def test_only_searches_specified_company(self, db):
        """只检索指定企业，不会混入其他企业数据"""
        # 企业 A 的分块
        for i in range(2):
            db.add(ChunkVector(
                document_id=1, company_id=10, chunk_index=i,
                content=f"企业A-{i}", embedding=json.dumps(_fake_vector()),
            ))
        # 企业 B 的分块
        for i in range(3):
            db.add(ChunkVector(
                document_id=2, company_id=20, chunk_index=i,
                content=f"企业B-{i}", embedding=json.dumps(_fake_vector()),
            ))
        db.commit()

        with patch("backend.rag.get_embedding") as mock_embed:
            mock_embed.return_value = [_fake_vector()]
            results = search_knowledge_base(company_id=10, query="任意")

        # 只返回企业 A 的结果
        assert all(r["content"].startswith("企业A") for r in results)


class TestSearchAPI:
    """POST /api/rag/search — 需要认证"""

    def test_search_requires_auth(self, client):
        """无 token → 403/401"""
        resp = client.post("/api/rag/search?query=test")
        assert resp.status_code in (403, 401)

    def test_search_with_auth(self, client):
        """有 token + 有数据 → 正常返回"""
        # 注册并获取 token
        reg = client.post("/api/auth/register", json={
            "name": "RAG测试", "email": "rag@test.com", "password": "123456",
        })
        token = reg.json()["access_token"]

        with patch("backend.rag.search_knowledge_base") as mock_search:
            mock_search.return_value = [
                {"chunk_id": 1, "document_id": 1, "content": "匹配内容", "score": 0.85},
            ]
            with patch("backend.rag.vector_store.count_chunks") as mock_count:
                mock_count.return_value = 100
                resp = client.post("/api/rag/search?query=如何",
                                   headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "如何"
        assert data["total_chunks"] == 100
        assert len(data["results"]) == 1

    def test_stats_requires_auth(self, client):
        """GET /api/rag/stats 需要认证"""
        resp = client.get("/api/rag/stats")
        assert resp.status_code in (403, 401)
