from dataclasses import asdict

from fastapi import APIRouter, Depends, Response

from app.api.dependencies import Auth, CurrentUser
from app.api.rate_limit import enforce_login_limit
from app.api.schemas.auth import LoginInput, RefreshInput, RegisterInput, TokenResponse
from app.api.schemas.users import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=UserResponse)
async def register(body: RegisterInput, auth: Auth) -> UserResponse:
    user = await auth.register(str(body.email), body.name, body.password)
    return UserResponse.model_validate(user)


@router.post(
    "/login", response_model=TokenResponse, dependencies=[Depends(enforce_login_limit)]
)
async def login(body: LoginInput, auth: Auth) -> TokenResponse:
    return TokenResponse(**asdict(await auth.login(str(body.email), body.password)))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshInput, auth: Auth) -> TokenResponse:
    return TokenResponse(**asdict(await auth.refresh(body.refresh_token)))


@router.post("/logout", status_code=204)
async def logout(body: RefreshInput, auth: Auth) -> Response:
    await auth.logout(body.refresh_token)
    return Response(status_code=204)


@router.post("/logout-all", status_code=204)
async def logout_all(user_id: CurrentUser, auth: Auth) -> Response:
    await auth.logout_all(user_id)
    return Response(status_code=204)
