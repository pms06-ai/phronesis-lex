"""
URL Configuration for Phronesis LEX Backend.

Comprehensive REST API for forensic legal document analysis.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django_backend.cases.views import CaseViewSet, CaseNoteViewSet
from django_backend.documents.views import (
    DocumentViewSet, CaseDocumentViewSet,
    ProfessionalViewSet, ProfessionalCapacityViewSet
)
from django_backend.analysis.views import (
    ClaimViewSet, ContradictionViewSet, BiasSignalViewSet,
    TimelineEventViewSet, ToulminArgumentViewSet, EntityViewSet,
    LegalRuleViewSet, BiasBaselineViewSet, AnalysisRunViewSet,
    CaseContradictionViewSet, CaseBiasViewSet
)


# API Root view
@api_view(['GET'])
def api_root(request):
    """API root with documentation."""
    return Response({
        'name': 'Phronesis LEX API',
        'version': '5.0',
        'description': 'Forensic Case Intelligence Platform for UK Family Court',
        'endpoints': {
            'cases': '/api/cases/',
            'documents': '/api/documents/',
            'claims': '/api/claims/',
            'contradictions': '/api/contradictions/',
            'bias-signals': '/api/bias-signals/',
            'timeline': '/api/timeline/',
            'arguments': '/api/arguments/',
            'entities': '/api/entities/',
            'legal-rules': '/api/legal-rules/',
            'bias-baselines': '/api/bias-baselines/',
            'analysis-runs': '/api/analysis-runs/',
            'dashboard': '/api/cases/dashboard/',
        },
        'documentation': 'See /admin/ for Django admin interface'
    })


# Main router
router = DefaultRouter()
router.register(r'cases', CaseViewSet, basename='case')
router.register(r'case-notes', CaseNoteViewSet, basename='case-note')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'professionals', ProfessionalViewSet, basename='professional')
router.register(r'professional-capacities', ProfessionalCapacityViewSet, basename='professional-capacity')
router.register(r'claims', ClaimViewSet, basename='claim')
router.register(r'contradictions', ContradictionViewSet, basename='contradiction')
router.register(r'bias-signals', BiasSignalViewSet, basename='bias-signal')
router.register(r'timeline', TimelineEventViewSet, basename='timeline')
router.register(r'arguments', ToulminArgumentViewSet, basename='argument')
router.register(r'entities', EntityViewSet, basename='entity')
router.register(r'legal-rules', LegalRuleViewSet, basename='legal-rule')
router.register(r'bias-baselines', BiasBaselineViewSet, basename='bias-baseline')
router.register(r'analysis-runs', AnalysisRunViewSet, basename='analysis-run')

# Nested routers for case-scoped resources
cases_router = nested_routers.NestedDefaultRouter(router, r'cases', lookup='case')
cases_router.register(r'documents', CaseDocumentViewSet, basename='case-documents')
cases_router.register(r'claims', ClaimViewSet, basename='case-claims')
cases_router.register(r'contradictions', CaseContradictionViewSet, basename='case-contradictions')
cases_router.register(r'bias-signals', CaseBiasViewSet, basename='case-bias')
cases_router.register(r'timeline', TimelineEventViewSet, basename='case-timeline')
cases_router.register(r'arguments', ToulminArgumentViewSet, basename='case-arguments')
cases_router.register(r'entities', EntityViewSet, basename='case-entities')
cases_router.register(r'analysis-runs', AnalysisRunViewSet, basename='case-analysis-runs')
cases_router.register(r'notes', CaseNoteViewSet, basename='case-notes')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API root
    path('api/', api_root, name='api-root'),
    
    # Router URLs
    path('api/', include(router.urls)),
    path('api/', include(cases_router.urls)),
    
    # Custom case actions
    path(
        'api/cases/<uuid:pk>/stats/',
        CaseViewSet.as_view({'get': 'stats'}),
        name='case-stats'
    ),
    path(
        'api/cases/<uuid:pk>/analyze/',
        CaseViewSet.as_view({'post': 'analyze'}),
        name='case-analyze'
    ),
    path(
        'api/cases/<uuid:pk>/summary/',
        CaseViewSet.as_view({'get': 'summary'}),
        name='case-summary'
    ),
    path(
        'api/cases/dashboard/',
        CaseViewSet.as_view({'get': 'dashboard'}),
        name='case-dashboard'
    ),
    
    # Contradiction detection
    path(
        'api/cases/<uuid:case_pk>/detect-contradictions/',
        CaseContradictionViewSet.as_view({'post': 'detect'}),
        name='case-detect-contradictions'
    ),
    path(
        'api/cases/<uuid:case_pk>/contradiction-summary/',
        CaseContradictionViewSet.as_view({'get': 'summary'}),
        name='case-contradiction-summary'
    ),
    
    # Bias analysis
    path(
        'api/cases/<uuid:case_pk>/bias-report/',
        CaseBiasViewSet.as_view({'get': 'report'}),
        name='case-bias-report'
    ),
    
    # Entity graph
    path(
        'api/cases/<uuid:case_pk>/entity-graph/',
        EntityViewSet.as_view({'get': 'graph'}),
        name='case-entity-graph'
    ),
    
    # Argument generation
    path(
        'api/cases/<uuid:case_pk>/generate-arguments/',
        ToulminArgumentViewSet.as_view({'post': 'generate'}),
        name='case-generate-arguments'
    ),
    
    # Timeline conflicts
    path(
        'api/cases/<uuid:case_pk>/timeline/conflicts/',
        TimelineEventViewSet.as_view({'get': 'conflicts'}),
        name='case-timeline-conflicts'
    ),
    
    # Document stats
    path(
        'api/cases/<uuid:case_pk>/documents/stats/',
        CaseDocumentViewSet.as_view({'get': 'stats'}),
        name='case-documents-stats'
    ),
    
    # Contradiction resolve
    path(
        'api/contradictions/<uuid:pk>/resolve/',
        ContradictionViewSet.as_view({'post': 'resolve'}),
        name='contradiction-resolve'
    ),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
