"""
向量存储和检索：基于 NumPy 的余弦相似度搜索
"""
import json
import numpy as np
from sqlalchemy.orm import Session
from backend.models import SessionLocal, ChunkVector


class VectorStore:
    """向量检索（NumPy 实现，零外部依赖）"""

    def add_chunks(
        self,
        document_id: int,
        company_id: int,
        chunks: list[str],
        vectors: list[list[float]],
        db: Session | None = None,
    ):
        """批量添加文档分块和向量"""
        _close = db is None
        if db is None:
            db = SessionLocal()
        try:
            for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
                record = ChunkVector(
                    document_id=document_id,
                    company_id=company_id,
                    chunk_index=i,
                    content=chunk,
                    embedding=json.dumps(vec),
                    token_count=len(chunk),
                )
                db.add(record)
            db.commit()
        finally:
            if _close:
                db.close()

    def search(
        self,
        company_id: int,
        query_vector: list[float],
        top_k: int = 3,
        db: Session | None = None,
    ) -> list[dict]:
        """余弦相似度检索，返回 top_k 个最相关片段"""
        _close = db is None
        if db is None:
            db = SessionLocal()
        try:
            records = (
                db.query(ChunkVector)
                .filter(ChunkVector.company_id == company_id)
                .all()
            )
            if not records:
                return []

            query_vec = np.array(query_vector, dtype=np.float32)
            stored_vecs = np.array(
                [json.loads(r.embedding) for r in records],
                dtype=np.float32,
            )

            # 余弦相似度
            query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
            stored_norms = stored_vecs / (np.linalg.norm(stored_vecs, axis=1, keepdims=True) + 1e-8)
            similarities = np.dot(stored_norms, query_norm)

            # Top-K
            top_indices = np.argsort(similarities)[::-1][:top_k]

            results = []
            for idx in top_indices:
                if similarities[idx] > 0.3:
                    results.append({
                        "chunk_id": records[idx].id,
                        "document_id": records[idx].document_id,
                        "content": records[idx].content,
                        "score": float(similarities[idx]),
                    })
            return results
        finally:
            if _close:
                db.close()

    def delete_by_document(self, document_id: int, db: Session | None = None):
        """删除某文档的所有分块"""
        _close = db is None
        if db is None:
            db = SessionLocal()
        try:
            db.query(ChunkVector).filter(ChunkVector.document_id == document_id).delete()
            db.commit()
        finally:
            if _close:
                db.close()

    def count_chunks(self, company_id: int, db: Session | None = None) -> int:
        """统计某企业的分块数量"""
        _close = db is None
        if db is None:
            db = SessionLocal()
        try:
            return db.query(ChunkVector).filter(ChunkVector.company_id == company_id).count()
        finally:
            if _close:
                db.close()


# 全局单例
vector_store = VectorStore()
