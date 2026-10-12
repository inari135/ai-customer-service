"""
文档上传和解析：路由层（业务逻辑在 services/knowledge_service.py）
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from backend.auth import get_current_company
from backend.models import Company, get_db
from backend.schemas import DocumentInfo, UploadResponse, MessageResponse
from backend.services.knowledge_service import (
    upload_document,
    list_documents,
    delete_document,
)

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
def upload(
    file: UploadFile = File(...),
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """上传知识库文档"""
    content = file.file.read()
    return upload_document(company, file.filename, content, db)


@router.get("/list", response_model=list[DocumentInfo])
def list_docs(
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
) -> list[DocumentInfo]:
    """获取知识库文档列表"""
    return list_documents(company, db)


@router.delete("/{document_id}", response_model=MessageResponse)
def delete(
    document_id: int,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """删除知识库文档"""
    return delete_document(document_id, company, db)
