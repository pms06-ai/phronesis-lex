"""FCIP Analysis Engines."""

from .entity_resolution import EntityResolutionEngine, EntityRoster, ResolutionResult
from .temporal import TemporalParser, CourtCalendar, TemporalRelation
from .argumentation import ArgumentationEngine, LegalRule, LEGAL_RULES
from .bias import BiasDetectionEngine, BiasBaseline, BaselineCorpus
from .contradiction import (
    ContradictionDetectionEngine,
    ContradictionType,
    Contradiction,
    ContradictionReport,
)
# Alias for compatibility
ContradictionEngine = ContradictionDetectionEngine

__all__ = [
    "EntityResolutionEngine",
    "EntityRoster",
    "ResolutionResult",
    "TemporalParser",
    "CourtCalendar",
    "TemporalRelation",
    "ArgumentationEngine",
    "LegalRule",
    "LEGAL_RULES",
    "BiasDetectionEngine",
    "BiasBaseline",
    "BaselineCorpus",
    "ContradictionEngine",
    "ContradictionDetectionEngine",
    "ContradictionType",
    "Contradiction",
    "ContradictionReport",
]
