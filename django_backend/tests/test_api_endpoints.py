"""
Tests for API endpoints.
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestCasesAPI:
    """Test cases API endpoints."""

    def test_list_cases(self, authenticated_client, case):
        """Test listing cases."""
        response = authenticated_client.get('/api/cases/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 1

    def test_create_case(self, authenticated_client):
        """Test creating a case."""
        response = authenticated_client.post('/api/cases/', {
            'reference': 'NEW/2024/001',
            'case_type': 'public_law',
            'court_level': 'family_court',
            'status': 'active',
            'title': 'New Test Case'
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['reference'] == 'NEW/2024/001'

    def test_get_case(self, authenticated_client, case):
        """Test retrieving a single case."""
        response = authenticated_client.get(f'/api/cases/{case.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['reference'] == case.reference

    def test_update_case(self, authenticated_client, case):
        """Test updating a case."""
        response = authenticated_client.patch(f'/api/cases/{case.id}/', {
            'status': 'closed'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'closed'

    def test_delete_case(self, authenticated_client, case):
        """Test deleting a case."""
        response = authenticated_client.delete(f'/api/cases/{case.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestClaimsAPI:
    """Test claims API endpoints."""

    def test_list_claims_for_case(self, authenticated_client, claims, case):
        """Test listing claims for a case."""
        response = authenticated_client.get(f'/api/cases/{case.id}/claims/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_filter_claims_by_modality(self, authenticated_client, claims, case):
        """Test filtering claims by modality."""
        response = authenticated_client.get(f'/api/cases/{case.id}/claims/', {
            'modality': 'alleged'
        })
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['modality'] == 'alleged'

    def test_filter_claims_by_certainty(self, authenticated_client, claims, case):
        """Test filtering claims by minimum certainty."""
        response = authenticated_client.get(f'/api/cases/{case.id}/claims/', {
            'min_certainty': '0.8'
        })
        assert response.status_code == status.HTTP_200_OK
        for claim in response.data['results']:
            assert claim['certainty'] >= 0.8

    def test_invalid_certainty_filter(self, authenticated_client, case):
        """Test that invalid certainty filter is handled gracefully."""
        response = authenticated_client.get(f'/api/cases/{case.id}/claims/', {
            'min_certainty': 'invalid'
        })
        # Should not crash, returns all claims
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestContradictionsAPI:
    """Test contradictions API endpoints."""

    def test_detect_contradictions(self, authenticated_client, claims, case):
        """Test running contradiction detection."""
        response = authenticated_client.post(f'/api/cases/{case.id}/detect-contradictions/')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]
        assert 'run_id' in response.data

    def test_get_contradiction_summary(self, authenticated_client, case):
        """Test getting contradiction summary."""
        response = authenticated_client.get(f'/api/cases/{case.id}/contradiction-summary/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total' in response.data
        assert 'by_type' in response.data
        assert 'by_severity' in response.data


@pytest.mark.django_db
class TestAuditLog:
    """Test audit logging functionality."""

    def test_audit_log_created_on_resolve(self, authenticated_client, claims, case):
        """Test that resolving a contradiction creates an audit log."""
        from django_backend.analysis.models import Contradiction
        from django_backend.core.models import AuditLog

        # First run detection to create contradictions
        authenticated_client.post(f'/api/cases/{case.id}/detect-contradictions/')

        # Get a contradiction
        contradiction = Contradiction.objects.filter(case=case).first()
        if contradiction:
            initial_count = AuditLog.objects.count()

            # Resolve it
            response = authenticated_client.post(
                f'/api/contradictions/{contradiction.id}/resolve/',
                {'note': 'Test resolution'}
            )
            assert response.status_code == status.HTTP_200_OK

            # Check audit log was created
            assert AuditLog.objects.count() > initial_count
