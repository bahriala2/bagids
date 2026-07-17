"""Routes d'authentification."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from hitl.backend.auth import authenticate, create_access_token, current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate(form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect")
    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer",
            "user": {"username": user["username"], "role": user["role"],
                     "full_name": user["full_name"]}}


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return user
