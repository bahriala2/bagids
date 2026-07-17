"""
BAg-IDS HITL — Authentification et contrôle d'accès multi-rôles.

Trois rôles hiérarchisés :
  - reader  : consultation seule (dashboard, incidents, audit) ;
  - analyst : reader + approuver/rejeter les incidents en attente ;
  - admin   : analyst + gouvernance (paramètres, toggle HITL, agents).

JWT (HS256) porté par l'en-tête Authorization: Bearer <token>.
"""

from __future__ import annotations

import datetime as _dt
from typing import Callable

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from hitl.backend.config import CONFIG

# Rang des rôles (un rôle supérieur inclut les permissions inférieures)
ROLE_RANK = {"reader": 0, "analyst": 1, "admin": 2}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def _hash_pw(password: str) -> bytes:
    # bcrypt limite le secret à 72 octets : on tronque explicitement.
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt())


def _verify_pw(password: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], hashed)
    except ValueError:
        return False


# Table des utilisateurs (mots de passe hachés au chargement du module)
_USERS: dict[str, dict] = {}
for u in CONFIG["users"]:
    _USERS[u["username"]] = {
        "username": u["username"],
        "full_name": u.get("full_name", u["username"]),
        "role": u["role"],
        "password_hash": _hash_pw(u["password"]),
    }


def authenticate(username: str, password: str) -> dict | None:
    user = _USERS.get(username)
    if not user or not _verify_pw(password, user["password_hash"]):
        return None
    return user


def create_access_token(user: dict) -> str:
    now = _dt.datetime.now(_dt.timezone.utc)
    payload = {
        "sub": user["username"],
        "role": user["role"],
        "name": user["full_name"],
        "iat": now,
        "exp": now + _dt.timedelta(minutes=CONFIG["access_token_minutes"]),
    }
    return jwt.encode(payload, CONFIG["jwt_secret"],
                      algorithm=CONFIG["jwt_algorithm"])


def current_user(token: str = Depends(oauth2_scheme)) -> dict:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou session expirée",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, CONFIG["jwt_secret"],
                             algorithms=[CONFIG["jwt_algorithm"]])
    except jwt.PyJWTError:
        raise cred_exc
    username = payload.get("sub")
    if username not in _USERS:
        raise cred_exc
    return {"username": username, "role": payload.get("role"),
            "full_name": payload.get("name")}


def require_role(min_role: str) -> Callable:
    """Dépendance FastAPI : exige au moins le rôle `min_role`."""
    threshold = ROLE_RANK[min_role]

    def _dep(user: dict = Depends(current_user)) -> dict:
        if ROLE_RANK.get(user["role"], -1) < threshold:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle '{min_role}' requis (vous êtes '{user['role']}')")
        return user
    return _dep
