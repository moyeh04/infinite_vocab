# Infinite Vocab Backend API Tests

A comprehensive Bruno API test suite for the Infinite Vocab backend application.

## Quick Start

1. **Prerequisites**
   - [Bruno](https://www.usebruno.com/) installed
   - Firebase emulator running (`firebase emulators:start`)
   - Backend server running (`python app.py`)

2. **Import Collection**
   - Open Bruno
   - Import this folder (`tests/api/Infinite_Vocab_Backend/`)
   - The environment is automatically configured via `environments/env.bru`

3. **Run Tests**
   - Execute the full collection in Bruno
   - Tests run in sequence (folder numbers 1-4 indicate execution order)
   - All dynamic variables (tokens, IDs) are automatically set by tests

## Test Structure

```plaintext
1_health/     - Health check endpoint
2_auth/       - Authentication (emulator user creation & login)
3_users/      - User management tests
4_words/      - Word CRUD operations
```

## Environment Variables

The tests use these variables (auto-configured in `environments/env.bru`):

- `apiUrl`: `http://localhost:5000`
- `authUrl`: `http://localhost:9099`
- `testEmail`: `testuser@example.com`
- `testPassword`: `testpassword123`

Dynamic variables like `{{idToken}}` and `{{wordId}}` are set automatically by tests.

## Test Coverage

**Essential CRUD Operations:**

- Create, read, update, delete words
- Add descriptions and examples
- Star words
- User authentication and management

**Validation & Error Handling:**

- Missing/empty fields
- Invalid authentication
- Resource not found
- Duplicate entries

All tests expect camelCase responses and validate proper HTTP status codes.
