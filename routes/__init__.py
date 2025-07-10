# Routes package - HTTP endpoint handlers


from .category_routes import category_bp
from .user_routes import user_bp
from .word_category_routes import word_category_bp
from .word_routes import words_bp

__all__ = ["user_bp", "words_bp", "category_bp", "word_category_bp"]
