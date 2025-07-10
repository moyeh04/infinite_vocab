# Routes package - HTTP endpoint handlers


from .admin_routes import admin_bp
from .category_routes import category_bp
from .search_routes import search_bp
from .user_routes import user_bp
from .word_category_routes import word_category_bp
from .word_routes import words_bp

__all__ = [
    "admin_bp",
    "category_bp",
    "search_bp",
    "user_bp",
    "word_category_bp",
    "words_bp",
]
