"""Autenticação de contas e emissão de tokens de acesso."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

_password_hash = PasswordHash.recommended()
_bearer = HTTPBearer(auto_error=False)
_TOKEN_LIFETIME = timedelta(hours=12)


def _secret() -> str:
    """Obtém segredo forte do ambiente; nunca usa chave padrão insegura."""
    value = os.getenv("AMAZONIA_AUTH_SECRET", "")
    if len(value) < 32:
        raise HTTPException(status_code=503, detail="Autenticação indisponível: configure AMAZONIA_AUTH_SECRET com pelo menos 32 caracteres.")
    return value


def hash_password(password: str) -> str:
    """Armazena senha usando Argon2id com parâmetros recomendados pela biblioteca."""
    return _password_hash.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    """Compara senha informada com o hash persistido."""
    try:
        return _password_hash.verify(password, encoded_hash)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: str) -> str:
    """Emite token HS256 com validade limitada a doze horas."""
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": user_id, "iat": now, "exp": now + _TOKEN_LIFETIME},
        _secret(),
        algorithm="HS256",
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Valida token e retorna usuário ativo; falhas não revelam detalhes internos."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticação necessária.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized
    try:
        payload = jwt.decode(credentials.credentials, _secret(), algorithms=["HS256"])
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id:
            raise unauthorized
    except (jwt.InvalidTokenError, HTTPException):
        raise unauthorized
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user
