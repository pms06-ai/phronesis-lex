"""
Custom Exception Handler for Phronesis LEX
Provides secure, user-friendly error responses without leaking internal details.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import (
    ValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    Throttled,
)

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that:
    1. Logs errors with full details for debugging
    2. Returns sanitized responses to clients
    3. Provides consistent error format
    """
    # Get the standard error response
    response = exception_handler(exc, context)

    # Get request info for logging
    request = context.get('request')
    view = context.get('view')
    view_name = view.__class__.__name__ if view else 'Unknown'

    # Handle Django ValidationError
    if isinstance(exc, DjangoValidationError):
        response = Response(
            {'error': 'Validation error', 'details': exc.messages if hasattr(exc, 'messages') else str(exc)},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Handle cases where DRF didn't create a response
    if response is None:
        # Log the full exception for debugging
        logger.exception(
            f"Unhandled exception in {view_name}",
            extra={
                'view': view_name,
                'path': request.path if request else 'Unknown',
                'method': request.method if request else 'Unknown',
                'user': str(request.user) if request and hasattr(request, 'user') else 'Anonymous',
            }
        )

        # Return generic error to client
        response = Response(
            {
                'error': 'An unexpected error occurred',
                'code': 'internal_error',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    else:
        # Log handled exceptions at appropriate level
        if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            logger.info(f"Auth failure in {view_name}: {exc}")
        elif isinstance(exc, PermissionDenied):
            logger.warning(f"Permission denied in {view_name}: {exc}")
        elif isinstance(exc, NotFound):
            logger.debug(f"Not found in {view_name}: {exc}")
        elif isinstance(exc, Throttled):
            logger.warning(f"Rate limit exceeded in {view_name}")
        elif isinstance(exc, ValidationError):
            logger.debug(f"Validation error in {view_name}: {exc}")
        else:
            logger.warning(f"Handled exception in {view_name}: {exc}")

        # Standardize response format
        if response.data:
            error_data = {
                'error': _get_error_message(exc),
                'code': _get_error_code(exc),
            }

            # Include validation details for ValidationError
            if isinstance(exc, ValidationError) and isinstance(response.data, dict):
                error_data['details'] = response.data

            response.data = error_data

    return response


def _get_error_message(exc):
    """Get user-friendly error message."""
    if isinstance(exc, NotAuthenticated):
        return 'Authentication required'
    elif isinstance(exc, AuthenticationFailed):
        return 'Invalid authentication credentials'
    elif isinstance(exc, PermissionDenied):
        return 'You do not have permission to perform this action'
    elif isinstance(exc, NotFound):
        return 'Resource not found'
    elif isinstance(exc, Throttled):
        return f'Request throttled. Try again in {exc.wait} seconds'
    elif isinstance(exc, ValidationError):
        return 'Invalid request data'
    else:
        return str(exc) if hasattr(exc, '__str__') else 'An error occurred'


def _get_error_code(exc):
    """Get error code for programmatic handling."""
    if isinstance(exc, NotAuthenticated):
        return 'not_authenticated'
    elif isinstance(exc, AuthenticationFailed):
        return 'authentication_failed'
    elif isinstance(exc, PermissionDenied):
        return 'permission_denied'
    elif isinstance(exc, NotFound):
        return 'not_found'
    elif isinstance(exc, Throttled):
        return 'throttled'
    elif isinstance(exc, ValidationError):
        return 'validation_error'
    else:
        return 'error'
