class UserError(Exception):
    """Base for all user-domain exceptions."""


class UsernameAlreadyTakenError(UserError):
    def __init__(self, username: str) -> None:
        super().__init__(f"Username '{username}' is already taken")
