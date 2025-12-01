"""
Input Validators for Phronesis LEX
Centralized validation utilities.
"""
from rest_framework import serializers


def validate_float_range(value, min_val=0.0, max_val=1.0, field_name='value'):
    """Validate a float is within a range."""
    try:
        float_val = float(value)
        if float_val < min_val or float_val > max_val:
            raise serializers.ValidationError(
                f"{field_name} must be between {min_val} and {max_val}"
            )
        return float_val
    except (TypeError, ValueError):
        raise serializers.ValidationError(
            f"{field_name} must be a valid number"
        )


def validate_certainty(value):
    """Validate certainty score (0.0-1.0)."""
    return validate_float_range(value, 0.0, 1.0, 'certainty')


def validate_confidence(value):
    """Validate confidence score (0.0-1.0)."""
    return validate_float_range(value, 0.0, 1.0, 'confidence')


def validate_z_score(value):
    """Validate z-score (typically -10 to 10)."""
    return validate_float_range(value, -100.0, 100.0, 'z_score')


def validate_positive_int(value, field_name='value'):
    """Validate positive integer."""
    try:
        int_val = int(value)
        if int_val < 0:
            raise serializers.ValidationError(
                f"{field_name} must be a positive integer"
            )
        return int_val
    except (TypeError, ValueError):
        raise serializers.ValidationError(
            f"{field_name} must be a valid integer"
        )


def safe_float(value, default=None):
    """Safely convert to float, return default on failure."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=None):
    """Safely convert to int, return default on failure."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_bool(value, default=False):
    """Safely convert to bool."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)
