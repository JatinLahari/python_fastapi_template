from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from auth.dependencies import get_current_user
from auth.jwt import create_access_token, create_refresh_token, decode_token
from auth.password import hash_password, verify_password
from db.database import get_db
from models import (
    AccessTokenResponse,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    serialize_id,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(data: UserCreate, db=Depends(get_db)):
    """
    Register a new user account.
    """
    existing = await db["users"].find_one({"email": data.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    now = datetime.now(timezone.utc)
    user_doc = {
        "_id": str(ObjectId()),
        "name": data.name,
        "email": data.email,
        "password": hash_password(data.password),
        "phone_number": data.phone_number,
        "role": data.role.value,
        "academy_id": data.academy_id,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    await db["users"].insert_one(user_doc)
    return UserResponse(**user_doc)


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive access + refresh tokens",
)
async def login(data: UserLogin, db=Depends(get_db)):
    """
    Authenticate a user and return a JWT access token and refresh token.
    """
    user = await db["users"].find_one({"email": data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email.",
        )

    if not verify_password(data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact support.",
        )

    token_payload = {
        "sub": user["_id"],
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
    }
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token({"sub": user["_id"]})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------
@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Get a new access token using a refresh token",
)
async def refresh_token(body: RefreshRequest, db=Depends(get_db)):
    """
    Exchange a valid refresh token for a new access token.
    """
    payload = decode_token(body.refresh_token)
    user_id: str = payload.get("sub")

    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )

    token_payload = {
        "sub": user["_id"],
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
    }
    new_access_token = create_access_token(token_payload)
    return AccessTokenResponse(access_token=new_access_token)


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------
@router.post(
    "/logout",
    summary="Logout (client-side token removal)",
    status_code=status.HTTP_200_OK,
)
async def logout(_: dict = Depends(get_current_user)):
    """
    Logout the current user.
    """
    return {"message": "Logged out successfully. Please remove tokens from client storage."}
