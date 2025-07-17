# Technical Debt & Refactoring Roadmap

This document outlines the known technical debt and potential areas for improvement in the codebase. These items are prioritized based on their impact on consistency, maintainability, and code quality.

## 🟩 Recently Completed: Major Architectural Improvements

- [x] **Word Module Architecture Refactor** ✅ **COMPLETED v2.0.0**
  - **Previous State**: 774-line monolithic `services/word_service.py` with manual JSON parsing, dictionary-based data handling, and massive code duplication
  - **Current State**: Clean domain-separated architecture with proper separation of concerns:
    - `services/word/word_service.py` (190 lines) - Core word CRUD operations
    - `services/word/description_service.py` (200 lines) - Description CRUD operations  
    - `services/word/example_service.py` (192 lines) - Example CRUD operations
    - `services/word/star_service.py` (63 lines) - Star and milestone logic
  - **Improvements Achieved**:
    - ✅ Eliminated 600+ lines of code duplication
    - ✅ Applied proper separation of concerns following Domain-Driven Design
    - ✅ Fixed DAL layer to return Pydantic models consistently (like category service)
    - ✅ Each service now matches category service patterns (~150-200 lines)
    - ✅ Maintained full backward compatibility
    - ✅ Consistent error handling and logging patterns
  - **Business Impact**: Transformed the largest feature module from maintenance nightmare to clean, maintainable architecture

- [x] **Case-Insensitive Search Implementation** ✅ **COMPLETED**
  - **Previous State**: Forced lowercase normalization that destroyed user's original capitalization
  - **Current State**: Dedicated search fields (`word_text_search`, `category_name_search`) enable case-insensitive search while preserving original capitalization
  - **Improvements**: Users can search for "javascript" and find "JavaScript" entries while maintaining display quality

## 🟨 Medium Priority: Remaining Architectural Consistency

- [ ] **Implement Factory-Level Ownership Pattern Across All Services**
  - **Current State**: Each service has its own ownership verification logic with some duplication
  - **Target State**: Centralized ownership verification in factory layer following Domain-Driven Design principles
  - **Scope**: Apply to `word`, `category`, `user`, `search`, and `word_category` services
  - **Benefits**: Single source of truth, DRY principle compliance, improved testability
  - **Technical Approach**: Add `verify_entity_ownership()` method to respective factories

- [x] **Remove Legacy Response Helpers Completely** ✅ **COMPLETED**
  - **Previous State**: `utils/response_helpers.py` contained deprecated `camelized_response()` and `decamelized_request()` functions
  - **Current State**: File completely removed, all references eliminated from codebase
  - **Verification**: No active code references legacy helpers (only documentation mentions remain)
  - **Impact**: Eliminated dependency on `pyhumps` library and manual case conversion

- [x] **Standardize Import Structure Across Codebase** ✅ **COMPLETED**
  - **Previous State**: Direct imports bypassing `__init__.py` files (e.g., `from models.word_models import Word`)
  - **Current State**: All imports use proper module structure through `__init__.py` files (e.g., `from models import Word`)
  - **Scope**: Fixed imports in services, factories, DAL, and all other modules
  - **Benefits**: Better encapsulation, cleaner dependencies, easier refactoring, industry-standard practices

## 🟨 Medium Priority: Code Quality & Consistency

- [x] **Standardize Logging Across All Modules** ✅ **COMPLETED**

  - **Issue**: ~~The legacy `words` module (DAL, Service, Routes) uses `print()` statements for logging.~~
  - **Resolution**: ✅ Implemented comprehensive structured logging system with:
    - Centralized logger configuration with environment-based log levels
    - Request/response middleware with timing and sanitization
    - Consistent logging across all layers (routes, services, DAL, middleware)
    - All print statements replaced with structured logger calls
    - Performance monitoring with @timed_execution decorator
    - Proper error logging with stack traces (exc_info=True)
    - Layer-specific prefixes (ROUTE, SERVICE, DAL, AUTH, CONFIG, FACTORY)
    - Security features: PII redaction and request body truncation
    - **Fixed duplicate request logging issue** by consolidating logging after authentication

- [ ] **Remove Redundant Exception Handling**
  - **Issue**: Some services contain `try...except` blocks that catch a custom exception only to re-raise it immediately (e.g., `except NotFoundError: raise`).
  - **Task**: Review services and remove these redundant blocks. Allow specific, caught exceptions to bubble up to the route layer where they are handled appropriately.

## 🟩 Low Priority: Polish & Future Enhancements

### Polish

- [ ] **Case-Insensitive Admin User Search**: The `find_user_by_code` service should normalize the input code to uppercase before querying to ensure a match, as codes are stored in uppercase.
- [ ] **Improve Docstrings**: Ensure all functions and modules have consistent and descriptive docstrings.

### Potential Future Features (Backlog)

- [ ] **Pagination**: Implement cursor-based or offset-based pagination for all list endpoints (`GET /words`, `GET /admin/users`) to handle large datasets efficiently.
- [ ] **Advanced Search Fields**: For a more robust search, consider adding dedicated lowercase fields in Firestore (e.g., `word_text_search`) to allow case-insensitive searching without affecting the display casing of the original data.
- [ ] **Category Descriptions**: Add an optional `description` field to categories for better organization by users.
- [ ] **Full Test Suite**: Develop a comprehensive suite of unit and integration tests to ensure long-term stability and catch regressions.
- [ ] **Explore Full-Text Search (Learning)**: Research and experiment with Firestore full-text search integration (Algolia/Elasticsearch) for advanced search capabilities like fuzzy matching, synonyms, and content search within descriptions/examples. This is for learning purposes and future enhancement consideration.
