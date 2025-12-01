"""
Pytest configuration and fixtures for Phronesis LEX tests.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client."""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def case(db, user):
    """Create a test case."""
    from django_backend.cases.models import Case
    return Case.objects.create(
        reference='TEST/2024/001',
        case_type='private_law',
        court_level='family_court',
        status='active',
        title='Test Case for Unit Tests'
    )


@pytest.fixture
def document(db, case):
    """Create a test document."""
    from django_backend.documents.models import Document
    return Document.objects.create(
        case=case,
        filename='test_document.pdf',
        document_type='statement',
        author='Test Author',
        status='completed',
        content='This is test content for the document.'
    )


@pytest.fixture
def claims(db, case, document):
    """Create test claims."""
    from django_backend.analysis.models import Claim
    claims = [
        Claim.objects.create(
            case=case,
            document=document,
            claim_text='The father visited the child on Monday.',
            claim_type='assertion',
            modality='asserted',
            polarity='affirmative',
            certainty=0.8,
            asserted_by='Test Author',
            subject='father'
        ),
        Claim.objects.create(
            case=case,
            document=document,
            claim_text='The father did not visit the child on Monday.',
            claim_type='assertion',
            modality='asserted',
            polarity='negative',
            certainty=0.9,
            asserted_by='Test Author',
            subject='father'
        ),
        Claim.objects.create(
            case=case,
            document=document,
            claim_text='The mother reported abuse allegations.',
            claim_type='allegation',
            modality='alleged',
            polarity='affirmative',
            certainty=0.6,
            asserted_by='Social Worker',
            subject='mother'
        ),
    ]
    return claims
