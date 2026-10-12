"""
认证模块：企业注册、登录、JWT 中间件
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from backend.config import settings
from backend.models import Company, get_db
from backend.schemas import CompanyRegister, CompanyLogin, TokenResponse, CompanyInfo

router = APIRouter()

# JWT Bearer
security = HTTPBearer()


def hash_password(password: str) -> str:
    """PBKDF2 + SHA256 密码哈希"""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}${hashed.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """验证密码"""
    try:
        salt, hash_hex = stored_hash.split("$", 1)
        new_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
        return new_hash.hex() == hash_hex
    except (ValueError, AttributeError):
        return False


def create_token(company_id: int, email: str) -> str:
    """生成 JWT"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(company_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """验证 JWT，返回 payload"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证令牌")


def get_current_company(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Company:
    """依赖注入：从请求头 Bearer Token 中获取当前企业"""
    payload = verify_token(credentials.credentials)
    company_id = int(payload.get("sub"))
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="企业不存在")
    return company


# --- 路由 ---

@router.post("/register", response_model=TokenResponse)
def register(req: CompanyRegister, db: Session = Depends(get_db)):
    """企业注册"""
    existing = db.query(Company).filter(Company.email == req.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该邮箱已注册")

    company = Company(
        name=req.name,
        email=req.email,
        password_hash=hash_password(req.password),
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    token = create_token(company.id, company.email)
    return TokenResponse(
        access_token=token,
        company_id=company.id,
        company_name=company.name,
    )


@router.post("/login", response_model=TokenResponse)
def login(req: CompanyLogin, db: Session = Depends(get_db)):
    """企业登录"""
    company = db.query(Company).filter(Company.email == req.email).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")

    if not verify_password(req.password, company.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")

    token = create_token(company.id, company.email)
    return TokenResponse(
        access_token=token,
        company_id=company.id,
        company_name=company.name,
    )


@router.get("/me", response_model=CompanyInfo)
def me(company: Company = Depends(get_current_company)):
    """获取当前登录企业信息"""
    return {
        "id": company.id,
        "name": company.name,
        "email": company.email,
        "welcome_message": company.welcome_message,
        "ai_tone": company.ai_tone,
    }
