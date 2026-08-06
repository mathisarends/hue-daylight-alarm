import os

# Importing the API modules requires a configured JWT signing secret.
os.environ.setdefault("AUTH_JWT_SECRET", "test-jwt-secret")
