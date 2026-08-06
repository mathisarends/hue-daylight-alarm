class InvalidAccessTokenError(Exception):
    """The bearer token is missing, malformed, expired, or has a bad signature."""
