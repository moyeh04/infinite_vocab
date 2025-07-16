# Technical Debt & Refactoring Roadmap

This document outlines the known technical debt and potential areas for improvement in the codebase. These items are prioritized based on their impact on consistency, maintainability, and code quality.

## 🟥 High Priority: Core Architectural Refactor

**Critical Issue**: The application currently has two conflicting architectural patterns that create maintenance overhead and inconsistent developer experience.

- [ ] **Migrate the `words` Module to the Modern Pydantic Architecture**
  - **Current State**: The `words` module uses manual JSON parsing, `pyhumps` case conversion, and dictionary-based data handling
  - **Target State**: Align with the modern pattern used by `users` and `categories` modules that leverage Pydantic for type safety, automatic validation, and serialization
  - **Business Impact**: This is the largest feature module and its inconsistency affects development velocity and code maintainability
  - **Technical Sub-tasks:**
    - [ ] **Create Pydantic Models**: `Word`, `Description`, `Example` models with proper field aliases for camelCase/snake_case conversion
    - [ ] **Create Request Schemas**: `WordCreateSchema`, `WordUpdateSchema`, `DescriptionSchema`, `ExampleSchema` for input validation
    - [ ] **Refactor Service Layer**: Replace dictionary returns with typed Pydantic model instances
    - [ ] **Refactor Route Layer**: Replace manual `request.get_json()` + `decamelized_request()` with Pydantic schema validation
    - [ ] **Remove Legacy Dependencies**: Eliminate `camelized_response()`, `decamelized_request()`, and `pyhumps` dependency
  - **Success Criteria**: All modules use identical architectural patterns, zero usage of `response_helpers.py`

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
