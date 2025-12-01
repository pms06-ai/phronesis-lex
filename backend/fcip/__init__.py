"""
FCIP - Forensic Case Intelligence Platform
Integrated into Phronesis LEX

Engines:
- Entity Resolution (RapidFuzz matching)
- Temporal Logic (Allen intervals, UK court calendar)
- Argumentation (Toulmin structures with legal rules)
- Bias Detection (z-score statistical analysis)
"""

from .config import FCIPConfig

__version__ = "5.0.0"
__all__ = ["FCIPConfig"]
