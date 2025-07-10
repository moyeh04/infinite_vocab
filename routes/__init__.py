# Routes package - HTTP endpoint handlers

from .user_routes import user_bp
from .word_routes import words_bp

__all__ = ["user_bp", "words_bp"]
