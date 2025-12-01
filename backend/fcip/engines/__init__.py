"""FCIP Analysis Engines."""

from .entity_resolution import EntityResolutionEngine, EntityRoster, ResolutionResult
from .temporal import TemporalParser, CourtCalendar, TemporalRelation
from .argumentation import ArgumentationEngine, LegalRule, LEGAL_RULES
from .bias import BiasDetectionEngine, BiasBaseline, BaselineCorpus
from .contradiction import (
    ContradictionEngine,
    ContradictionType,
    Contradiction,
    ContradictionReport,
    detect_contradictions_from_db,
)

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
    "ContradictionType",
    "Contradiction",
    "ContradictionReport",
    "detect_contradictions_from_db",
]
