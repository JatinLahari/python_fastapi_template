from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from auth.jwt import decode_token
from db.database import get_db

# ---------------------------------------------------------------------------
# OAuth2 token scheme — token is expected at Authorization: Bearer <token>
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db=Depends(get_db),
) -> dict:
    """
    FastAPI dependency that:
    1. Extracts the Bearer token from the request header.
    2. Decodes & validates the JWT (raises 401 on failure).
    3. Looks up the user in MongoDB and returns the document.
    """
    payload = decode_token(token)
    user_id: str = payload.get("sub")

    user = await db["users"].find_one({"_id": user_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )
    return user


def require_roles(*roles: str):
    """
    Role-based access control factory.
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(roles)}",
            )
        return user

    return role_checker
