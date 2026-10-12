"""
RAG 检索模块：问题 → 向量化 → 相似度搜索 → 返回相关片段
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.auth import get_current_company
from backend.models import Company, get_db
from backend.embedding import get_embedding
from backend.vector_store import vector_store
from backend.schemas import SearchResponse, StatsResponse

router = APIRouter()


def search_knowledge_base(company_id: int, query: str, top_k: int = 3) -> list[dict]:
    """检索知识库：查询 → Embedding → 向量搜索 → 返回 Top-K 片段"""
    # 1. 查询向量化
    vectors = get_embedding([query])
    query_vec = vectors[0]

    # 2. 向量检索
    results = vector_store.search(company_id, query_vec, top_k)
    return results


@router.post("/search", response_model=SearchResponse)
def search(
    query: str,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """API 接口：检索知识库"""
    results = search_knowledge_base(company.id, query)
    return {
        "query": query,
        "total_chunks": vector_store.count_chunks(company.id, db=db),
        "results": results,
    }


@router.get("/stats", response_model=StatsResponse)
def stats(
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """API 接口：知识库统计"""
    from backend.models import Document
    doc_count = db.query(Document).filter(Document.company_id == company.id).count()
    chunk_count = vector_store.count_chunks(company.id, db=db)
    return {
        "document_count": doc_count,
        "chunk_count": chunk_count,
    }
