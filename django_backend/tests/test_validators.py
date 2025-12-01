"""
Tests for input validators.
"""
import pytest
from rest_framework import serializers
from django_backend.core.validators import (
    validate_float_range,
    validate_certainty,
    validate_confidence,
    safe_float,
    safe_int,
    safe_bool,
)


class TestValidators:
    """Test validation utilities."""

    def test_validate_float_range_valid(self):
        """Test valid float values pass validation."""
        assert validate_float_range(0.5, 0.0, 1.0) == 0.5
        assert validate_float_range(0.0, 0.0, 1.0) == 0.0
        assert validate_float_range(1.0, 0.0, 1.0) == 1.0
        assert validate_float_range('0.75', 0.0, 1.0) == 0.75

    def test_validate_float_range_invalid(self):
        """Test invalid float values raise ValidationError."""
        with pytest.raises(serializers.ValidationError):
            validate_float_range(1.5, 0.0, 1.0)
        with pytest.raises(serializers.ValidationError):
            validate_float_range(-0.1, 0.0, 1.0)
        with pytest.raises(serializers.ValidationError):
            validate_float_range('invalid', 0.0, 1.0)

    def test_validate_certainty(self):
        """Test certainty validation (0-1 range)."""
        assert validate_certainty(0.5) == 0.5
        with pytest.raises(serializers.ValidationError):
            validate_certainty(1.5)

    def test_validate_confidence(self):
        """Test confidence validation (0-1 range)."""
        assert validate_confidence(0.8) == 0.8
        with pytest.raises(serializers.ValidationError):
            validate_confidence(-0.1)

    def test_safe_float_valid(self):
        """Test safe_float with valid inputs."""
        assert safe_float('0.5') == 0.5
        assert safe_float(0.5) == 0.5
        assert safe_float('1.0') == 1.0

    def test_safe_float_invalid(self):
        """Test safe_float returns default for invalid inputs."""
        assert safe_float('invalid') is None
        assert safe_float('invalid', 0.0) == 0.0
        assert safe_float(None) is None
        assert safe_float(None, 0.5) == 0.5

    def test_safe_int_valid(self):
        """Test safe_int with valid inputs."""
        assert safe_int('42') == 42
        assert safe_int(42) == 42
        assert safe_int('0') == 0

    def test_safe_int_invalid(self):
        """Test safe_int returns default for invalid inputs."""
        assert safe_int('invalid') is None
        assert safe_int('invalid', 0) == 0
        assert safe_int(None) is None
        assert safe_int('3.14') is None  # Not an integer

    def test_safe_bool_valid(self):
        """Test safe_bool with valid inputs."""
        assert safe_bool('true') is True
        assert safe_bool('True') is True
        assert safe_bool('1') is True
        assert safe_bool('yes') is True
        assert safe_bool('false') is False
        assert safe_bool('0') is False
        assert safe_bool(True) is True
        assert safe_bool(False) is False

    def test_safe_bool_default(self):
        """Test safe_bool returns default for None."""
        assert safe_bool(None) is False
        assert safe_bool(None, True) is True
