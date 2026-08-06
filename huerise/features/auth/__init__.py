from huerise.presentation import Feature

from .infrastructure.di import AuthProvider
from .presentation import auth_router, register_auth_exception_handlers

feature = Feature(
    name="auth",
    routers=[auth_router],
    providers=[AuthProvider],
    register_exception_handlers=register_auth_exception_handlers,
)

__all__ = ["feature"]
