"""
Background Tasks for Phronesis LEX
Uses Huey for async task execution.
"""
import logging
from huey.contrib.djhuey import task, db_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@db_task()
def run_contradiction_detection(case_id: str, run_id: str):
    """
    Run contradiction detection as a background task.

    Args:
        case_id: UUID of the case to analyze
        run_id: UUID of the AnalysisRun to update
    """
    from django_backend.cases.models import Case
    from django_backend.analysis.models import Claim, AnalysisRun
    from django_backend.analysis.services import ContradictionDetectionService

    try:
        case = Case.objects.get(pk=case_id)
        run = AnalysisRun.objects.get(pk=run_id)

        run.status = 'running'
        run.progress_message = 'Loading claims...'
        run.progress_percent = 5
        run.save()

        # Get claims
        claims = Claim.objects.filter(case=case).select_related('document')
        claims_count = claims.count()

        if claims_count < 2:
            run.status = 'completed'
            run.completed_at = timezone.now()
            run.progress_message = 'Not enough claims to analyze'
            run.progress_percent = 100
            run.save()
            return {'status': 'completed', 'contradictions_found': 0}

        run.progress_message = f'Analyzing {claims_count} claims...'
        run.progress_percent = 10
        run.save()

        # Run detection
        service = ContradictionDetectionService()
        candidates = service.detect_contradictions(claims, str(case_id))

        run.progress_message = f'Found {len(candidates)} potential contradictions, saving...'
        run.progress_percent = 80
        run.save()

        # Save to database
        claims_by_id = {str(c.id): c for c in claims}
        created_count = service.save_contradictions(candidates, case, claims_by_id)

        run.status = 'completed'
        run.completed_at = timezone.now()
        run.contradictions_found = created_count
        run.claims_extracted = claims_count
        run.progress_percent = 100
        run.progress_message = f'Detection complete: {created_count} contradictions found'
        run.save()

        logger.info(f"Contradiction detection completed for case {case_id}: {created_count} found")
        return {'status': 'completed', 'contradictions_found': created_count}

    except Exception as e:
        logger.exception(f"Contradiction detection failed for case {case_id}")
        try:
            run = AnalysisRun.objects.get(pk=run_id)
            run.mark_failed(str(e))
        except Exception:
            pass
        return {'status': 'failed', 'error': str(e)}


@db_task()
def run_bias_detection(case_id: str, run_id: str):
    """Run bias detection as a background task."""
    from django_backend.cases.models import Case
    from django_backend.documents.models import Document
    from django_backend.analysis.models import AnalysisRun
    from django_backend.analysis.services import BiasDetectionService

    try:
        case = Case.objects.get(pk=case_id)
        run = AnalysisRun.objects.get(pk=run_id)

        run.status = 'running'
        run.progress_message = 'Loading documents...'
        run.progress_percent = 5
        run.save()

        documents = Document.objects.filter(case=case, status='completed')
        doc_count = documents.count()

        if doc_count == 0:
            run.status = 'completed'
            run.completed_at = timezone.now()
            run.progress_message = 'No processed documents to analyze'
            run.progress_percent = 100
            run.save()
            return {'status': 'completed', 'biases_detected': 0}

        run.progress_message = f'Analyzing {doc_count} documents for bias...'
        run.progress_percent = 20
        run.save()

        service = BiasDetectionService()
        total_biases = 0

        for i, doc in enumerate(documents):
            signals = service.analyze_document(doc, case)
            total_biases += len(signals)
            run.progress_percent = 20 + int(70 * (i + 1) / doc_count)
            run.save()

        run.status = 'completed'
        run.completed_at = timezone.now()
        run.biases_detected = total_biases
        run.documents_analyzed = doc_count
        run.progress_percent = 100
        run.progress_message = f'Bias detection complete: {total_biases} signals found'
        run.save()

        logger.info(f"Bias detection completed for case {case_id}: {total_biases} signals")
        return {'status': 'completed', 'biases_detected': total_biases}

    except Exception as e:
        logger.exception(f"Bias detection failed for case {case_id}")
        try:
            run = AnalysisRun.objects.get(pk=run_id)
            run.mark_failed(str(e))
        except Exception:
            pass
        return {'status': 'failed', 'error': str(e)}


@db_task()
def run_full_case_analysis(case_id: str, run_id: str):
    """Run complete case analysis pipeline."""
    from django_backend.cases.models import Case
    from django_backend.analysis.models import AnalysisRun

    try:
        case = Case.objects.get(pk=case_id)
        run = AnalysisRun.objects.get(pk=run_id)

        run.status = 'running'
        run.progress_message = 'Starting full case analysis...'
        run.progress_percent = 0
        run.save()

        # Step 1: Contradiction detection
        run.progress_message = 'Running contradiction detection...'
        run.progress_percent = 10
        run.save()

        from django_backend.analysis.models import Claim
        from django_backend.analysis.services import ContradictionDetectionService

        claims = Claim.objects.filter(case=case).select_related('document')
        if claims.count() >= 2:
            service = ContradictionDetectionService()
            candidates = service.detect_contradictions(claims, str(case_id))
            claims_by_id = {str(c.id): c for c in claims}
            contradictions_count = service.save_contradictions(candidates, case, claims_by_id)
            run.contradictions_found = contradictions_count

        run.progress_percent = 50
        run.save()

        # Step 2: Bias detection
        run.progress_message = 'Running bias detection...'
        run.progress_percent = 60
        run.save()

        from django_backend.documents.models import Document
        from django_backend.analysis.services import BiasDetectionService

        documents = Document.objects.filter(case=case, status='completed')
        bias_service = BiasDetectionService()
        total_biases = 0

        for doc in documents:
            signals = bias_service.analyze_document(doc, case)
            total_biases += len(signals)

        run.biases_detected = total_biases
        run.documents_analyzed = documents.count()
        run.claims_extracted = claims.count()

        run.status = 'completed'
        run.completed_at = timezone.now()
        run.progress_percent = 100
        run.progress_message = 'Full case analysis complete'
        run.save()

        logger.info(f"Full case analysis completed for case {case_id}")
        return {'status': 'completed'}

    except Exception as e:
        logger.exception(f"Full case analysis failed for case {case_id}")
        try:
            run = AnalysisRun.objects.get(pk=run_id)
            run.mark_failed(str(e))
        except Exception:
            pass
        return {'status': 'failed', 'error': str(e)}
