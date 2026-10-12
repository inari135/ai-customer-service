"""
Embedding 服务：调用外部 API 将文本转为向量
支持 OpenAI 和 Anthropic 两种 Embedding 提供商
"""
import numpy as np
from backend.config import settings


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """将长文本切分为固定大小的块，带重叠"""
    if not text.strip():
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def get_embedding(texts: list[str]) -> list[list[float]]:
    """调用 Embedding API 获取向量列表"""
    provider = settings.EMBEDDING_PROVIDER

    if provider == "siliconflow":
        return _siliconflow_embed(texts)
    elif provider == "openai":
        return _openai_embed(texts)
    else:
        raise ValueError(f"不支持的 Embedding 提供商：{provider}")


def _siliconflow_embed(texts: list[str]) -> list[list[float]]:
    """使用硅基流动 SiliconFlow Embedding API（OpenAI 兼容）"""
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.SILICONFLOW_API_KEY,
        base_url="https://api.siliconflow.cn/v1",
    )
    resp = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=texts,
    )
    return [d.embedding for d in resp.data]


def _openai_embed(texts: list[str]) -> list[list[float]]:
    """使用 OpenAI Embedding API"""
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    resp = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=texts,
    )
    return [d.embedding for d in resp.data]


def process_document(document_id: int, company_id: int, text: str) -> int:
    """
    完整流水线：分块 → 向量化 → 存入向量库
    返回分块数量
    """
    from backend.vector_store import vector_store

    # 1. 分块
    chunks = chunk_text(text)

    if not chunks:
        return 0

    # 2. 获取向量（分批，每批 20 条避免 API 限制）
    all_vectors = []
    batch_size = 20
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        vectors = get_embedding(batch)
        all_vectors.extend(vectors)

    # 3. 存入向量库
    vector_store.add_chunks(document_id, company_id, chunks, all_vectors)

    return len(chunks)
