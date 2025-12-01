"""
Prompt Generation System for Phronesis LEX

This module generates optimized prompts for copy-paste workflow with AI subscriptions.
Supports: Claude, ChatGPT, Grok, Perplexity, Le Chat, Venice AI

No API calls - designed for manual copy-paste workflow.
"""

from .generator import PromptGenerator
from .templates import PromptTemplates
from .parser import ResponseParser

__all__ = ["PromptGenerator", "PromptTemplates", "ResponseParser"]
