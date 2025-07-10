# Routes package - HTTP endpoint handlers

from .user_routes import user_bp
from .word_routes import words_bp
from .category_routes import category_bp

__all__ = ["user_bp", "words_bp", "category_bp"]
