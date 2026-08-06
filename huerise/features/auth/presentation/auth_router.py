from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from huerise.features.auth.application import AuthService
from huerise.features.auth.presentation.auth_schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"], route_class=DishkaRoute)


@auth_router.post(
    "/register", response_model=TokenResponse, status_code=201, operation_id="register"
)
async def register(
    body: RegisterRequest, auth_service: FromDishka[AuthService]
) -> TokenResponse:
    pair = await auth_service.register(body.username, body.password)
    return TokenResponse.from_domain(pair)


@auth_router.post("/login", response_model=TokenResponse, operation_id="login")
async def login(
    body: LoginRequest, auth_service: FromDishka[AuthService]
) -> TokenResponse:
    pair = await auth_service.login(body.username, body.password)
    return TokenResponse.from_domain(pair)


@auth_router.post("/refresh", response_model=TokenResponse, operation_id="refresh")
async def refresh(
    body: RefreshRequest, auth_service: FromDishka[AuthService]
) -> TokenResponse:
    pair = await auth_service.refresh(body.refresh_token)
    return TokenResponse.from_domain(pair)


@auth_router.post(
    "/logout", status_code=204, response_model=None, operation_id="logout"
)
async def logout(
    body: LogoutRequest, auth_service: FromDishka[AuthService]
) -> None:
    await auth_service.logout(body.refresh_token)
