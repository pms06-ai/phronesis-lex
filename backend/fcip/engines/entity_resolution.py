"""
FCIP v5.0 Entity Resolution Engine

Features:
- Pre-seeded entity roster from case professionals
- RapidFuzz fuzzy matching (token_sort_ratio)
- Role-based resolution patterns
- Pronoun co-reference tracking
- Alias learning and management
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

from ..config import config
from ..models.core import Entity, EntityType


# =============================================================================
# ROLE PATTERNS - UK Family Court
# =============================================================================

ROLE_PATTERNS: Dict[str, List[str]] = {
    "social_worker": [
        r"\b(?:the\s+)?(?:allocated\s+)?social\s+worker\b",
        r"\b(?:the\s+)?(?:children'?s?\s+)?social\s+worker\b",
        r"\bsw\b",
    ],
    "guardian": [
        r"\b(?:the\s+)?(?:children'?s?\s+)?guardian\b",
        r"\b(?:the\s+)?cafcass\s+(?:officer|guardian)\b",
        r"\bchildren'?s?\s+guardian\b",
    ],
    "judge": [
        r"\b(?:the\s+)?(?:learned\s+)?judge\b",
        r"\bhis\s+honou?r(?:\s+judge)?\b",
        r"\bher\s+honou?r(?:\s+judge)?\b",
        r"\bhhj\b",
        r"\bdjm?\b",
    ],
    "mother": [
        r"\bthe\s+mother\b",
        r"\bthe\s+(?:first\s+)?respondent\s+mother\b",
        r"\bm\b(?=\s+stated|\s+said|\s+reported)",
    ],
    "father": [
        r"\bthe\s+father\b",
        r"\bthe\s+(?:second\s+)?respondent\s+father\b",
        r"\bf\b(?=\s+stated|\s+said|\s+reported)",
    ],
    "child": [
        r"\bthe\s+child(?:ren)?\b",
        r"\bthe\s+subject\s+child(?:ren)?\b",
    ],
    "local_authority": [
        r"\bthe\s+local\s+authority\b",
        r"\bla\b",
        r"\b(?:the\s+)?applicant\s+(?:local\s+)?authority\b",
    ],
    "barrister": [
        r"\bcounsel\s+for\b",
        r"\blearned\s+counsel\b",
    ],
    "expert": [
        r"\bthe\s+(?:independent\s+)?expert\b",
        r"\bdr\.?\s+",
        r"\bprofessor\b",
    ],
}


@dataclass
class EntityResolutionConfig:
    """Configuration for entity resolution."""
    fuzzy_threshold: int = 88
    enable_pronoun_resolution: bool = True
    enable_role_resolution: bool = True
    min_name_length: int = 2


@dataclass
class ResolutionResult:
    """Result of entity resolution."""
    entity_id: Optional[UUID]
    matched_text: str
    match_type: str  # exact, fuzzy, role, alias, none
    confidence: float
    alternatives: List[Tuple[UUID, float]] = field(default_factory=list)
    role_matched: Optional[str] = None


@dataclass
class EntityRoster:
    """Pre-seeded roster of known entities for a case."""
    entities: Dict[UUID, Entity] = field(default_factory=dict)
    _name_index: Dict[str, List[UUID]] = field(default_factory=dict)
    _alias_index: Dict[str, UUID] = field(default_factory=dict)
    _role_assignments: Dict[str, UUID] = field(default_factory=dict)

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the roster."""
        self.entities[entity.entity_id] = entity

        # Index by canonical name
        key = entity.canonical_name.lower().strip()
        if key not in self._name_index:
            self._name_index[key] = []
        self._name_index[key].append(entity.entity_id)

        # Index aliases
        for alias in entity.aliases:
            alias_key = alias.lower().strip()
            self._alias_index[alias_key] = entity.entity_id

        # Index by role if single entity has that role
        for role in entity.roles:
            role_key = role.lower().strip()
            if role_key not in self._role_assignments:
                self._role_assignments[role_key] = entity.entity_id

    def get_by_role(self, role: str) -> Optional[Entity]:
        """Get entity by role if uniquely assigned."""
        role_key = role.lower().strip()
        if role_key in self._role_assignments:
            eid = self._role_assignments[role_key]
            return self.entities.get(eid)
        return None

    def get_all_names(self) -> List[str]:
        """Get all indexed names for fuzzy matching."""
        return list(self._name_index.keys())


class EntityResolutionEngine:
    """Engine for resolving entity mentions to known entities."""

    def __init__(
        self,
        roster: Optional[EntityRoster] = None,
        config: Optional[EntityResolutionConfig] = None
    ):
        self.roster = roster or EntityRoster()
        self.config = config or EntityResolutionConfig()
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile role patterns for efficiency."""
        compiled = {}
        for role, patterns in ROLE_PATTERNS.items():
            compiled[role] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled

    def resolve(self, text: str, context: Optional[str] = None) -> ResolutionResult:
        """
        Resolve a text mention to a known entity.

        Args:
            text: The entity mention to resolve
            context: Optional surrounding context for disambiguation

        Returns:
            ResolutionResult with match details
        """
        text = text.strip()
        if len(text) < self.config.min_name_length:
            return ResolutionResult(None, text, "none", 0.0)

        # 1. Exact match on canonical name
        key = text.lower()
        if key in self.roster._name_index:
            eid = self.roster._name_index[key][0]
            return ResolutionResult(eid, text, "exact", 1.0)

        # 2. Exact match on alias
        if key in self.roster._alias_index:
            eid = self.roster._alias_index[key]
            return ResolutionResult(eid, text, "alias", 0.95)

        # 3. Role-based resolution
        if self.config.enable_role_resolution:
            for role, patterns in self._compiled_patterns.items():
                for pattern in patterns:
                    if pattern.search(text):
                        entity = self.roster.get_by_role(role)
                        if entity:
                            return ResolutionResult(
                                entity.entity_id,
                                text,
                                "role",
                                0.85,
                                role_matched=role
                            )

        # 4. Fuzzy matching
        if RAPIDFUZZ_AVAILABLE:
            names = self.roster.get_all_names()
            if names:
                matches = process.extract(
                    key,
                    names,
                    scorer=fuzz.token_sort_ratio,
                    limit=3
                )
                alternatives = []
                for name, score, _ in matches:
                    if score >= self.config.fuzzy_threshold:
                        eid = self.roster._name_index[name][0]
                        alternatives.append((eid, score / 100))

                if alternatives:
                    best_eid, best_score = alternatives[0]
                    return ResolutionResult(
                        best_eid,
                        text,
                        "fuzzy",
                        best_score,
                        alternatives=alternatives[1:]
                    )

        return ResolutionResult(None, text, "none", 0.0)

    def resolve_all(self, texts: List[str]) -> Dict[str, ResolutionResult]:
        """Resolve multiple entity mentions."""
        return {text: self.resolve(text) for text in texts}

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the roster."""
        self.roster.add_entity(entity)

    def learn_alias(self, entity_id: UUID, alias: str) -> bool:
        """Learn a new alias for an existing entity."""
        if entity_id in self.roster.entities:
            alias_key = alias.lower().strip()
            self.roster._alias_index[alias_key] = entity_id
            return True
        return False

    def seed_from_professionals(self, professionals: List[dict]) -> int:
        """
        Seed the roster from Phronesis LEX professionals data.

        Args:
            professionals: List of professional dicts from database

        Returns:
            Number of entities added
        """
        count = 0
        for prof in professionals:
            prof_id = prof.get("id")
            entity = Entity(
                entity_id=UUID(prof_id) if prof_id else uuid4(),
                canonical_name=prof.get("name", "Unknown"),
                entity_type=self._map_profession_to_type(prof.get("profession", "")),
                roles=[prof.get("profession", "")],
                organisation=prof.get("organization"),
                aliases=prof.get("aliases", [])
            )
            self.add_entity(entity)
            count += 1
        return count

    def _map_profession_to_type(self, profession: str) -> EntityType:
        """Map profession string to EntityType."""
        profession_lower = profession.lower()
        mapping = {
            "social worker": EntityType.SOCIAL_WORKER,
            "guardian": EntityType.GUARDIAN,
            "judge": EntityType.JUDGE,
            "barrister": EntityType.BARRISTER,
            "solicitor": EntityType.SOLICITOR,
            "psychologist": EntityType.PSYCHOLOGIST,
            "expert": EntityType.EXPERT,
        }
        for key, etype in mapping.items():
            if key in profession_lower:
                return etype
        return EntityType.PERSON
