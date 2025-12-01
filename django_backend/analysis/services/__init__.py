"""Analysis services for Phronesis LEX."""
from .claim_extraction import ClaimExtractionService
from .contradiction_detection import ContradictionDetectionService
from .bias_detection import BiasDetectionService
from .argument_generation import ArgumentGenerationService

__all__ = [
    'ClaimExtractionService',
    'ContradictionDetectionService',
    'BiasDetectionService',
    'ArgumentGenerationService',
]

