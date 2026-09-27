from fastapi import APIRouter

from app.api.dependencies import CurrentUser, Users
from app.api.schemas.users import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def me(user_id: CurrentUser, users: Users) -> UserResponse:
    return UserResponse.model_validate(await users.get(user_id))


@router.patch("/me", response_model=UserResponse)
async def rename(body: UserUpdate, user_id: CurrentUser, users: Users) -> UserResponse:
    return UserResponse.model_validate(await users.rename(user_id, body.name))
