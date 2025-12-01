"""
Tests for authentication and authorization.
"""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestAuthentication:
    """Test authentication endpoints and authorization."""

    def test_unauthenticated_access_denied(self, api_client):
        """Test that unauthenticated requests are denied."""
        response = api_client.get('/api/cases/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_access_allowed(self, authenticated_client):
        """Test that authenticated requests are allowed."""
        response = authenticated_client.get('/api/cases/')
        assert response.status_code == status.HTTP_200_OK

    def test_token_obtain(self, api_client, user):
        """Test JWT token obtain endpoint."""
        response = api_client.post('/api/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_token_refresh(self, api_client, user):
        """Test JWT token refresh endpoint."""
        # First obtain tokens
        response = api_client.post('/api/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        refresh_token = response.data['refresh']

        # Then refresh
        response = api_client.post('/api/auth/token/refresh/', {
            'refresh': refresh_token
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_invalid_credentials(self, api_client):
        """Test that invalid credentials are rejected."""
        response = api_client.post('/api/auth/token/', {
            'username': 'invalid',
            'password': 'invalid'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_info_endpoint(self, authenticated_client, user):
        """Test user info endpoint returns correct data."""
        response = authenticated_client.get('/api/auth/user/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'
        assert response.data['email'] == 'test@example.com'

    def test_api_root_is_public(self, api_client):
        """Test that API root is publicly accessible."""
        response = api_client.get('/api/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Phronesis LEX API'
