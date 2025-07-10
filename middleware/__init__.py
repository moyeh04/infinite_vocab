# Middleware package - Authentication and request processing

from .firebase_auth_check import firebase_token_required

__all__ = ["firebase_token_required"]
