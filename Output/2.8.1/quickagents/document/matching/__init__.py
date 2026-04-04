"""
Matching engine for cross-referencing documents with source code.

Three-level matching architecture:
    Level 1: Convention matching (structured IDs, tags)
    Level 2: Keyword matching (synonyms, translations)
    Level 3: Semantic matching (LLM-powered)
"""

from .trace_engine import TraceMatchEngine
from .convention_matcher import ConventionMatcher
from .keyword_matcher import KeywordMatcher
from .semantic_matcher import SemanticMatcher
from .diff_analyzer import DiffAnalyzer
from .fix_suggester import FixSuggester
from .granularity import GranularityAdjuster
from .synonym_table import SynonymTable

__all__ = [
    "TraceMatchEngine",
    "ConventionMatcher",
    "KeywordMatcher",
    "SemanticMatcher",
    "DiffAnalyzer",
    "FixSuggester",
    "GranularityAdjuster",
    "SynonymTable",
]
