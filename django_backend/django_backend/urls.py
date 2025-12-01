"""URL configuration for Phronesis LEX backend."""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from django_backend.cases.views import CaseViewSet
from django_backend.documents.views import DocumentViewSet, CaseDocumentViewSet
from django_backend.analysis.views import (
    ClaimViewSet, ContradictionViewSet, BiasSignalViewSet,
    TimelineEventViewSet, ToulminArgumentViewSet, EntityViewSet,
    LegalRuleViewSet, AnalysisRunViewSet,
    CaseContradictionViewSet, CaseBiasViewSet,
)

# Main router
router = DefaultRouter()
router.register(r'cases', CaseViewSet, basename='case')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'claims', ClaimViewSet, basename='claim')
router.register(r'contradictions', ContradictionViewSet, basename='contradiction')
router.register(r'bias-signals', BiasSignalViewSet, basename='bias-signal')
router.register(r'timeline', TimelineEventViewSet, basename='timeline')
router.register(r'arguments', ToulminArgumentViewSet, basename='argument')
router.register(r'entities', EntityViewSet, basename='entity')
router.register(r'legal-rules', LegalRuleViewSet, basename='legal-rule')
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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/', include(cases_router.urls)),
    
    # Custom case actions
    path('api/cases/<uuid:case_pk>/stats/', CaseViewSet.as_view({'get': 'stats'}), name='case-stats'),
    path('api/cases/<uuid:case_pk>/analyze/', CaseViewSet.as_view({'post': 'analyze'}), name='case-analyze'),
    path('api/cases/<uuid:case_pk>/detect-contradictions/', 
         CaseContradictionViewSet.as_view({'post': 'detect'}), name='case-detect-contradictions'),
    path('api/cases/<uuid:case_pk>/contradiction-summary/', 
         CaseContradictionViewSet.as_view({'get': 'summary'}), name='case-contradiction-summary'),
    path('api/cases/<uuid:case_pk>/bias-report/', 
         CaseBiasViewSet.as_view({'get': 'report'}), name='case-bias-report'),
    path('api/cases/<uuid:case_pk>/entity-graph/', 
         EntityViewSet.as_view({'get': 'graph'}), name='case-entity-graph'),
    path('api/cases/<uuid:case_pk>/generate-arguments/', 
         ToulminArgumentViewSet.as_view({'post': 'generate'}), name='case-generate-arguments'),
]
