# Technical Debt & Refactoring Roadmap

This document outlines the known technical debt and potential areas for improvement in the codebase. These items are prioritized based on their impact on consistency, maintainability, and code quality.

## 🟥 High Priority: Core Architectural Refactor

The single most impactful improvement is to align the entire application on the "Modern" Pydantic-based architecture.

- [ ] **Migrate the `words` Module to the Modern Architecture**
  - The `words` feature currently uses a legacy pattern of manual validation and case-conversion helpers. It should be refactored to match the superior pattern used in the `categories` and `users` features.
  - **Sub-tasks:**
    - [ ] **Create `WordSchema` and `WordModel`:** Introduce Pydantic schemas for request validation (`POST`, `PATCH`) and a Pydantic model for data representation and response serialization. This includes models for the `description` and `example` sub-collections.
    - [ ] **Refactor `word_routes.py`:** Replace all manual request parsing (`request.get_json()`) and validation with Pydantic schema validation. Replace all calls to `camelized_response` and `decamelized_request` with `model.model_dump(by_alias=True)`.
    - [ ] **Refactor `word_service.py`:** Update the service to accept Pydantic schema objects and return Pydantic model instances instead of raw dictionaries.
    - [ ] **Deprecate `response_helpers.py`:** Once the `words` module is refactored, the `pyhumps`-based helper functions will no longer be needed and the file can be removed, simplifying the codebase.

## 🟨 Medium Priority: Code Quality & Consistency

- [ ] **Standardize Logging Across All Modules**

  - **Issue**: The legacy `words` module (DAL, Service, Routes) uses `print()` statements for logging.
  - **Task**: Replace all `print()` statements with the shared logger instance (`logger = logging.getLogger("infinite_vocab_app")`) to ensure structured, consistent logging throughout the application.

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
