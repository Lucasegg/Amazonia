"""Sessões web seguras com cookie HttpOnly e proteção CSRF."""
from __future__ import annotations

import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

_password_hash = PasswordHash.recommended()
_TOKEN_LIFETIME = timedelta(hours=12)
_SESSION_COOKIE = "amazonia_session"
_CSRF_COOKIE = "amazonia_csrf"


def _secret() -> str:
    value = os.getenv("AMAZONIA_AUTH_SECRET", "")
    if len(value) < 32:
        raise HTTPException(status_code=503, detail="Autenticação indisponível: configure AMAZONIA_AUTH_SECRET com pelo menos 32 caracteres.")
    return value


def _secure_cookie() -> bool:
    configured = os.getenv("AMAZONIA_COOKIE_SECURE")
    if configured is not None:
        return configured.strip().lower() in {"1", "true", "yes"}
    return os.getenv("VERCEL") == "1" or os.getenv("ENVIRONMENT", "").lower() == "production"


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        return _password_hash.verify(password, encoded_hash)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": user_id, "iat": now, "exp": now + _TOKEN_LIFETIME},
        _secret(),
        algorithm="HS256",
    )


def set_session_cookies(response: Response, user_id: str) -> None:
    """Cria sessão HttpOnly e token CSRF separado para double-submit."""
    secure = _secure_cookie()
    same_site = os.getenv("AMAZONIA_COOKIE_SAMESITE", "lax").lower()
    if same_site not in {"lax", "strict", "none"}:
        same_site = "lax"
    if same_site == "none" and not secure:
        raise HTTPException(status_code=500, detail="Cookies SameSite=None exigem HTTPS.")
    response.set_cookie(
        key=_SESSION_COOKIE,
        value=create_access_token(user_id),
        max_age=int(_TOKEN_LIFETIME.total_seconds()),
        httponly=True,
        secure=secure,
        samesite=same_site,
        path="/",
    )
    response.set_cookie(
        key=_CSRF_COOKIE,
        value=secrets.token_urlsafe(32),
        max_age=int(_TOKEN_LIFETIME.total_seconds()),
        httponly=False,
        secure=secure,
        samesite=same_site,
        path="/",
    )


def clear_session_cookies(response: Response) -> None:
    secure = _secure_cookie()
    same_site = os.getenv("AMAZONIA_COOKIE_SAMESITE", "lax").lower()
    response.delete_cookie(_SESSION_COOKIE, path="/", secure=secure, httponly=True, samesite=same_site)
    response.delete_cookie(_CSRF_COOKIE, path="/", secure=secure, httponly=False, samesite=same_site)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Valida sessão HttpOnly e exige CSRF para requisições de navegador."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticação necessária.",
    )
    origin = request.headers.get("origin")
    if origin:
        allowed = {
            item.strip()
            for item in os.getenv(
                "AMAZONIA_CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            ).split(",")
            if item.strip()
        }
        if origin not in allowed:
            raise HTTPException(status_code=403, detail="Origem não autorizada.")
        csrf_cookie = request.cookies.get(_CSRF_COOKIE, "")
        csrf_header = request.headers.get("x-csrf-token", "")
        if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
            raise HTTPException(status_code=403, detail="Validação CSRF obrigatória.")

    token = request.cookies.get(_SESSION_COOKIE)
    if not token:
        raise unauthorized
    try:
        payload = jwt.decode(token, _secret(), algorithms=["HS256"])
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id:
            raise unauthorized
    except jwt.InvalidTokenError:
        raise unauthorized
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user
