class AuthError(Exception):
    """Base for all auth-domain exceptions."""


class InvalidCredentialsError(AuthError):
    def __init__(self) -> None:
        super().__init__("Invalid username or password")


class InvalidRefreshTokenError(AuthError):
    def __init__(self) -> None:
        super().__init__("Invalid or expired refresh token")
