"""
Tests for contradiction detection service.
"""
import pytest
from django_backend.analysis.services import ContradictionDetectionService


@pytest.mark.django_db
class TestContradictionDetection:
    """Test contradiction detection functionality."""

    def test_detect_self_contradiction(self, claims):
        """Test detection of self-contradiction (same author, opposite polarity)."""
        service = ContradictionDetectionService()
        contradictions = service.detect_contradictions(claims, 'test-case-id')

        # Should find contradiction between claim 0 and 1 (same author, opposite statements)
        self_contradictions = [c for c in contradictions if c.same_author and c.contradiction_type == 'self']
        assert len(self_contradictions) >= 1

    def test_no_contradiction_different_subjects(self, db, case, document):
        """Test that claims about different subjects don't create contradictions."""
        from django_backend.analysis.models import Claim

        claims = [
            Claim.objects.create(
                case=case,
                document=document,
                claim_text='The father was present.',
                claim_type='assertion',
                modality='asserted',
                polarity='affirmative',
                certainty=0.8,
                asserted_by='Witness A',
                subject='father'
            ),
            Claim.objects.create(
                case=case,
                document=document,
                claim_text='The grandmother was not present.',
                claim_type='assertion',
                modality='asserted',
                polarity='negative',
                certainty=0.8,
                asserted_by='Witness B',
                subject='grandmother'
            ),
        ]

        service = ContradictionDetectionService()
        contradictions = service.detect_contradictions(claims, 'test-case-id')

        # Should not find direct contradiction (different subjects)
        direct = [c for c in contradictions if c.contradiction_type == 'direct']
        assert len(direct) == 0

    def test_modality_confusion_detection(self, db, case, document):
        """Test detection of modality confusion (allegation treated as fact)."""
        from django_backend.analysis.models import Claim

        claims = [
            Claim.objects.create(
                case=case,
                document=document,
                claim_text='The father abused the child.',
                claim_type='assertion',
                modality='asserted',
                polarity='affirmative',
                certainty=0.9,  # High certainty assertion
                asserted_by='Social Worker',
                subject='father'
            ),
            Claim.objects.create(
                case=case,
                document=document,
                claim_text='The father allegedly abused the child.',
                claim_type='allegation',
                modality='alleged',
                polarity='affirmative',
                certainty=0.5,
                asserted_by='Mother',
                subject='father'
            ),
        ]

        service = ContradictionDetectionService()
        contradictions = service.detect_contradictions(claims, 'test-case-id')

        modality = [c for c in contradictions if c.contradiction_type == 'modality']
        assert len(modality) >= 1

    def test_minimum_claims_required(self, db):
        """Test that detection requires at least 2 claims."""
        service = ContradictionDetectionService()

        # Empty list
        contradictions = service.detect_contradictions([], 'test-case-id')
        assert len(contradictions) == 0

        # Single claim
        from django_backend.analysis.models import Claim
        from django_backend.cases.models import Case
        case = Case.objects.create(reference='TEST/001', case_type='private_law')
        claim = Claim.objects.create(
            case=case,
            claim_text='Test claim',
            claim_type='assertion'
        )
        contradictions = service.detect_contradictions([claim], 'test-case-id')
        assert len(contradictions) == 0

    def test_save_contradictions(self, claims, case):
        """Test saving detected contradictions to database."""
        from django_backend.analysis.models import Contradiction

        service = ContradictionDetectionService()
        candidates = service.detect_contradictions(claims, str(case.id))

        claims_by_id = {str(c.id): c for c in claims}
        created = service.save_contradictions(candidates, case, claims_by_id)

        # Verify contradictions were saved
        assert created > 0
        assert Contradiction.objects.filter(case=case).count() == created

    def test_duplicate_prevention(self, claims, case):
        """Test that duplicate contradictions are not created."""
        from django_backend.analysis.models import Contradiction

        service = ContradictionDetectionService()
        candidates = service.detect_contradictions(claims, str(case.id))
        claims_by_id = {str(c.id): c for c in claims}

        # Save once
        first_count = service.save_contradictions(candidates, case, claims_by_id)

        # Save again
        second_count = service.save_contradictions(candidates, case, claims_by_id)

        # Should not create duplicates
        assert second_count == 0
        assert Contradiction.objects.filter(case=case).count() == first_count
