# TODO: Technical Debt & Code Quality Improvements

## High Priority (Affects Frontend Integration)
- [ ] **API Response Consistency**: Ensure all API responses properly convert snake_case to camelCase
- [ ] **Firestore Field Preservation**: Verify createdAt/updatedAt fields are preserved correctly
- [ ] **Error Response Format**: Standardize error response structure across all endpoints

## Medium Priority (Code Quality)
- [ ] **Remove Redundant Exception Handling**: Fix `except WordServiceError: raise` patterns in services
- [x] **Standardize Function Naming**: ~~Rename `usr_code` to `get_user_code`~~ and similar inconsistencies
- [ ] **Logging Migration**: Replace print statements with structured logging using `utils/logging_config.py`
- [ ] **Layer Identification**: Standardize prefixes (ROUTE:, DAL:, Service:) → use logger names instead

## Low Priority (Polish & Consistency)
- [ ] **Documentation**: Add comprehensive docstrings with consistent parameter naming
- [ ] **Input Validation**: Create consistent validation patterns across routes
- [ ] **Error Context**: Enhance error messages with consistent user_id/word_id context
- [ ] **Naming Convention Analysis**: Complete the cross-cutting naming convention audit
- [ ] **Exception Hierarchy**: Review and optimize custom exception usage
- [ ] **Performance Metrics**: Add performance metrics to logging
- [ ] **Enhanced Documentation**: Consider more comprehensive and detailed documentation in the future

## Future Features (Enhancement Backlog)
- [ ] **Category Descriptions**: Add optional description field to categories for better organization
- [ ] **Category Custom Ordering**: Allow users to set custom display order for categories
- [ ] **Category Alphabetical Sort**: Implement default alphabetical sorting for categories

## Code Locations to Address
- `services/word_service.py`: Lines with `except WordServiceError: raise`
- `routes/user_routes.py`: Function naming consistency
- `data_access/word_dal.py`: Print statement → logging migration
- `middleware/firebase_auth_check.py`: Error handling standardization
- All route files: Print statements → structured logging

## Notes
- Focus on new features first
- Technical debt items can be addressed incrementally
- API response consistency is critical for frontend integration
- Consider logging improvements during bug fixes or feature additions
- camelCase/snake_case conversion between frontend/backend is already working correctly
- Exception hierarchy and structure is well-designed
- Main focus should be on new features and fixing test inconsistencies
