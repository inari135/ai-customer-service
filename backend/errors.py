"""
统一错误处理：自定义异常 + 错误格式化
"""
from fastapi import HTTPException, status


class AppError:
    """应用层异常工厂，确保错误格式一致"""

    @staticmethod
    def not_found(resource: str, detail: str = "") -> HTTPException:
        msg = detail or f"{resource}不存在"
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)

    @staticmethod
    def bad_request(detail: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    @staticmethod
    def unauthorized(detail: str = "认证失败") -> HTTPException:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

    @staticmethod
    def forbidden(detail: str = "权限不足") -> HTTPException:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
