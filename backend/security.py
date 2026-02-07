# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from db.database import SessionLocal
from models import User, UserStatus, AuditLog


# =========================
# HASZOWANIE HASEŁ
# =========================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """
    Zwraca False zamiast wywalać 500, gdy hash jest pusty lub w nieobsługiwanym formacie
    (np. stare 'TEST_HASH' z dawnych seedów).
    """
    if not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        return False


# =========================
# JWT – USTAWIENIA
# =========================

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not set in environment")

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))


def create_access_token(user_id: int) -> str:
    expires_at = datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MINUTES)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# =========================
# AUDIT HELPERS
# =========================

def _get_ip(request: Request) -> str | None:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None


def _get_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


def _audit(db, *, action: str, request: Request, user_id: int | None, details: str | None = None) -> None:
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip=_get_ip(request),
        user_agent=_get_user_agent(request),
        details=details,
    )
    db.add(log)
    db.commit()


# =========================
# DEPENDENCY – AKTUALNY USER
# =========================

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MISSING_TOKEN")

    token = credentials.credentials

    db = SessionLocal()
    try:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        except ExpiredSignatureError:
            # spróbuj odczytać sub bez verify_exp tylko do loga
            user_id: int | None = None
            try:
                payload2 = jwt.decode(
                    token,
                    JWT_SECRET_KEY,
                    algorithms=[JWT_ALGORITHM],
                    options={"verify_exp": False},
                )
                sub = payload2.get("sub")
                if sub:
                    user_id = int(sub)
            except Exception:
                user_id = None

            _audit(db, action="TOKEN_EXPIRED", request=request, user_id=user_id, details=None)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="TOKEN_EXPIRED")

        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN")

        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN_PAYLOAD")

        user = db.query(User).filter(User.id == int(sub)).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER_NOT_FOUND")

        if user.status != UserStatus.ACTIVE.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ACCOUNT_INACTIVE")

        return user

    finally:
        db.close()


# =========================
# ROLE ENFORCEMENT (Depends)
# =========================

def require_role(*allowed_roles: str):
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_ROLE")
        return current_user
    return _checker
