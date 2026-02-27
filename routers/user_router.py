from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from auth.dependencies import get_current_user, require_roles
from auth.password import hash_password
from db.database import get_db
from models import UserResponse, UserUpdate, serialize_id

router = APIRouter(prefix="/users", tags=["Users"])


# ---------------------------------------------------------------------------
# GET /users/me  — Any authenticated user
# ---------------------------------------------------------------------------
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get your own profile",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)


# ---------------------------------------------------------------------------
# GET /users  — super_admin only
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Get all users (admin only)",
)
async def get_all_users(
    db=Depends(get_db),
    _: dict = Depends(require_roles("super_admin")),
):
    users = await db["users"].find().to_list(length=None)
    return [UserResponse(**u) for u in users]


# ---------------------------------------------------------------------------
# GET /users/{user_id}  — super_admin only
# ---------------------------------------------------------------------------
@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user by ID (admin only)",
)
async def get_user_by_id(
    user_id: str,
    db=Depends(get_db),
    _: dict = Depends(require_roles("super_admin")),
):
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found.",
        )
    return UserResponse(**user)


# ---------------------------------------------------------------------------
# PATCH /users/{user_id}  — super_admin can update anyone; users update themselves
# ---------------------------------------------------------------------------
@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user",
)
async def update_user(
    user_id: str,
    data: UserUpdate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "super_admin" and current_user["_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile.",
        )

    if (
        data.role is not None
        and data.role.value == "super_admin"
        and current_user["role"] != "super_admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super_admins can grant the super_admin role.",
        )

    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found.",
        )

    update_fields = data.model_dump(exclude_unset=True)
    if "password" in update_fields:
        update_fields["password"] = hash_password(update_fields["password"])
    if "role" in update_fields:
        update_fields["role"] = update_fields["role"].value if hasattr(update_fields["role"], "value") else update_fields["role"]

    update_fields["updated_at"] = datetime.now(timezone.utc)

    await db["users"].update_one({"_id": user_id}, {"$set": update_fields})
    updated_user = await db["users"].find_one({"_id": user_id})
    return UserResponse(**updated_user)


# ---------------------------------------------------------------------------
# DELETE /users/{user_id}  — super_admin only
# ---------------------------------------------------------------------------
@router.delete(
    "/{user_id}",
    summary="Delete a user (admin only)",
    status_code=status.HTTP_200_OK,
)
async def delete_user(
    user_id: str,
    db=Depends(get_db),
    _: dict = Depends(require_roles("super_admin")),
):
    result = await db["users"].delete_one({"_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found.",
        )
    return {"message": f"User '{user_id}' deleted successfully."}
