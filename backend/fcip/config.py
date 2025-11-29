"""FCIP Configuration - Integrated with Phronesis LEX."""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class FCIPConfig(BaseSettings):
    """FCIP configuration with sensible defaults for Phronesis LEX."""

    class Config:
        env_prefix = "FCIP_"
        extra = "ignore"

    # Entity Resolution
    entity_fuzzy_threshold: int = 88
    entity_fuzzy_algorithm: Literal["token_sort", "partial", "weighted"] = "token_sort"
    enable_pronoun_resolution: bool = True
    enable_role_resolution: bool = True

    # Temporal Logic
    enable_deadline_alerts: bool = True
    working_days_only: bool = True

    # Bias Detection
    bias_z_warning: float = 1.5
    bias_z_critical: float = 2.0
    bias_min_sample_size: int = 10

    # Argumentation
    enable_falsifiability: bool = True
    default_qualifier: str = "probably"

    # LLM Settings (uses existing Anthropic key)
    llm_temperature: float = 0.1
    llm_max_tokens: int = 8192

    # Confidence Calibration
    certainty_high_threshold: float = 0.85
    certainty_medium_threshold: float = 0.50
    certainty_low_threshold: float = 0.25


# Singleton instance
config = FCIPConfig()
