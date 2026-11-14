"""Sessões web seguras com cookie HttpOnly, CSRF e revogação persistente."""
from __future__ import annotations
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from pwdlib import PasswordHash
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuthAttempt, User

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

def _key_hash(scope: str, value: str) -> str:
    """Gera HMAC não reversível para não persistir e-mail ou IP em claro."""
    return hmac.new(_secret().encode(), f"{scope}:{value}".encode(), hashlib.sha256).hexdigest()

def is_rate_limited(db: Session, scope: str, value: str, limit: int, window: timedelta) -> bool:
    """Consulta limite persistido, compartilhado entre instâncias serverless."""
    cutoff = datetime.now(timezone.utc) - window
    key = _key_hash(scope, value)
    count = db.query(func.count(AuthAttempt.id)).filter(
        AuthAttempt.scope == scope, AuthAttempt.key_hash == key, AuthAttempt.attempted_at >= cutoff
    ).scalar() or 0
    return count >= limit

def record_auth_attempt(db: Session, scope: str, value: str) -> None:
    """Registra tentativa sem armazenar identificador pessoal em texto claro."""
    now = datetime.now(timezone.utc)
    db.query(AuthAttempt).filter(AuthAttempt.attempted_at < now - timedelta(days=2)).delete(synchronize_session=False)
    db.add(AuthAttempt(scope=scope, key_hash=_key_hash(scope, value), attempted_at=now))
    db.commit()

def clear_auth_attempts(db: Session, scope: str, value: str) -> None:
    """Remove falhas anteriores após autenticação bem-sucedida."""
    db.query(AuthAttempt).filter(AuthAttempt.scope == scope, AuthAttempt.key_hash == _key_hash(scope, value)).delete(synchronize_session=False)
    db.commit()

def create_access_token(user_id: str, session_version: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": user_id, "ver": session_version, "iat": now, "exp": now + _TOKEN_LIFETIME},
        _secret(), algorithm="HS256",
    )

def set_csrf_cookie(response: Response, token: str | None = None) -> str:
    """Emite token CSRF acessível apenas ao JavaScript da origem da API."""
    secure = _secure_cookie()
    same_site = os.getenv("AMAZONIA_COOKIE_SAMESITE", "lax").lower()
    if same_site not in {"lax", "strict", "none"}:
        same_site = "lax"
    if same_site == "none" and not secure:
        raise HTTPException(status_code=500, detail="Cookies SameSite=None exigem HTTPS.")
    value = token or secrets.token_urlsafe(32)
    response.set_cookie(key=_CSRF_COOKIE, value=value, max_age=int(_TOKEN_LIFETIME.total_seconds()),
        httponly=False, secure=secure, samesite=same_site, path="/")
    return value

def set_session_cookies(response: Response, user_id: str, session_version: int) -> str:
    """Cria sessão HttpOnly e retorna CSRF para uso em memória no cliente."""
    secure = _secure_cookie()
    same_site = os.getenv("AMAZONIA_COOKIE_SAMESITE", "lax").lower()
    if same_site not in {"lax", "strict", "none"}:
        same_site = "lax"
    if same_site == "none" and not secure:
        raise HTTPException(status_code=500, detail="Cookies SameSite=None exigem HTTPS.")
    response.set_cookie(key=_SESSION_COOKIE, value=create_access_token(user_id, session_version),
        max_age=int(_TOKEN_LIFETIME.total_seconds()), httponly=True, secure=secure, samesite=same_site, path="/")
    return set_csrf_cookie(response)

def clear_session_cookies(response: Response) -> None:
    secure = _secure_cookie()
    same_site = os.getenv("AMAZONIA_COOKIE_SAMESITE", "lax").lower()
    response.delete_cookie(_SESSION_COOKIE, path="/", secure=secure, httponly=True, samesite=same_site)
    response.delete_cookie(_CSRF_COOKIE, path="/", secure=secure, httponly=False, samesite=same_site)

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Valida sessão, versão de revogação e CSRF para operações de navegador."""
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticação necessária.")
    origin = request.headers.get("origin")
    if origin:
        allowed = {item.strip() for item in os.getenv("AMAZONIA_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if item.strip()}
        if origin not in allowed:
            raise HTTPException(status_code=403, detail="Origem não autorizada.")
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            csrf_cookie = request.cookies.get(_CSRF_COOKIE, "")
            csrf_header = request.headers.get("x-csrf-token", "")
            if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
                raise HTTPException(status_code=403, detail="Validação CSRF obrigatória.")
    token = request.cookies.get(_SESSION_COOKIE)
    if not token:
        raise unauthorized
    try:
        payload = jwt.decode(token, _secret(), algorithms=["HS256"])
        user_id, version = payload.get("sub"), payload.get("ver")
        if not isinstance(user_id, str) or not user_id or not isinstance(version, int):
            raise unauthorized
    except jwt.InvalidTokenError:
        raise unauthorized
    user = db.get(User, user_id)
    if user is None or user.session_version != version:
        raise unauthorized
    return user
