"""
Response helpers for consistent API formatting.
Handles snake_case (Python) to camelCase (frontend) conversion.
"""

import humps
from flask import jsonify


def decamelized_request(request_data):
    """
    Convert camelCase request data to snake_case for Python processing.
    Preserves Firestore timestamp fields (createdAt, updatedAt) as-is.

    Args:
        request_data: Dictionary with camelCase keys from frontend

    Returns:
        Dictionary with snake_case keys for Python code
    """
    if not request_data:
        return {}

    def _preserve_firestore_fields(data):
        """Recursively preserve Firestore timestamp fields while decamelizing others."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Preserve Firestore timestamp fields
                if key in ["createdAt", "updatedAt"]:
                    result[key] = _preserve_firestore_fields(value)
                else:
                    # Convert key to snake_case, recursively process value
                    snake_key = humps.decamelize(key)
                    result[snake_key] = _preserve_firestore_fields(value)
            return result
        elif isinstance(data, list):
            return [_preserve_firestore_fields(item) for item in data]
        else:
            return data

    return _preserve_firestore_fields(request_data)


def camelized_response(data, status_code=200):
    """
    Convert snake_case keys to camelCase and return Flask response.
    Preserves Firestore timestamp fields (createdAt, updatedAt) as-is.

    Args:
        data: Dictionary or list to convert and return
        status_code: HTTP status code (default: 200)

    Returns:
        Flask JSON response with camelCase keys
    """

    def _preserve_firestore_fields(data):
        """Recursively preserve Firestore timestamp fields while camelizing others."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Preserve Firestore timestamp fields
                if key in ["createdAt", "updatedAt"]:
                    result[key] = _preserve_firestore_fields(value)
                else:
                    # Convert key to camelCase, recursively process value
                    camel_key = humps.camelize(key)
                    result[camel_key] = _preserve_firestore_fields(value)
            return result
        elif isinstance(data, list):
            return [_preserve_firestore_fields(item) for item in data]
        else:
            return data

    camelized_data = _preserve_firestore_fields(data)
    return jsonify(camelized_data), status_code


def error_response(message, status_code=500, context=None):
    """
    Standard error response format.

    Args:
        message: Error message string
        status_code: HTTP status code
        context: Optional additional context

    Returns:
        Flask JSON response with camelCase keys
    """
    error_data = {"error": message}
    if context:
        error_data["context"] = context

    return camelized_response(error_data, status_code)
