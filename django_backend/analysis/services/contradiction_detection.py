"""
Contradiction Detection Service
Cross-references claims to identify contradictions using semantic similarity.
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import re
from uuid import UUID

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer, util
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available. Using fallback similarity.")


@dataclass
class ContradictionCandidate:
    """A potential contradiction between two claims."""
    claim_a_id: UUID
    claim_b_id: UUID
    contradiction_type: str
    confidence: float
    semantic_similarity: float
    description: str
    legal_significance: Optional[str] = None
    recommended_action: Optional[str] = None
    temporal_conflict: bool = False
    same_author: bool = False


class ContradictionDetectionService:
    """
    Service for detecting contradictions across claims.
    
    Uses semantic similarity and logical rules to identify:
    - Direct contradictions
    - Self-contradictions
    - Temporal impossibilities
    - Modality confusion
    - Value mismatches
    """
    
    # Thresholds
    SIMILARITY_THRESHOLD = 0.65
    HIGH_SIMILARITY_THRESHOLD = 0.85
    
    # Negation patterns for UK legal language
    NEGATION_PATTERNS = [
        r"\bdid not\b", r"\bdidn't\b", r"\bnot\b", r"\bnever\b",
        r"\bdoes not\b", r"\bdoesn't\b", r"\bwas not\b", r"\bwasn't\b",
        r"\bno\b", r"\bnone\b", r"\bdenies?\b", r"\bdenied\b",
        r"\bhas not\b", r"\bhasn't\b", r"\bcannot\b", r"\bcan't\b",
        r"\bwill not\b", r"\bwon't\b", r"\brefuses?\b", r"\brefused\b",
    ]
    
    # Legal significance templates
    LEGAL_SIGNIFICANCE = {
        'direct': (
            "Direct contradictions may indicate unreliable evidence. "
            "Consider raising in cross-examination with reference to both statements."
        ),
        'self': (
            "Self-contradictions are significant under the Lucas direction (R v Lucas [1981]). "
            "The court must consider why the author gave inconsistent accounts before drawing "
            "conclusions about their credibility. Per Re H-C [2016] EWCA Civ 136."
        ),
        'modality': (
            "Treating allegations as established facts breaches Re B [2008] UKHL 35. "
            "Unproved allegations cannot form the foundation for findings. "
            "The standard of proof is the balance of probabilities."
        ),
        'temporal': (
            "Temporal impossibilities suggest either fabrication or confusion. "
            "Create a detailed timeline exhibit and require clarification before the court "
            "can rely on either account."
        ),
        'value': (
            "Inconsistent values for the same attribute indicate unreliable evidence. "
            "Seek corroborating documentation to verify which value is correct."
        ),
        'attribution': (
            "Attribution conflicts require resolution through independent evidence. "
            "Consider requesting disclosure of any recordings or contemporaneous notes."
        ),
    }
    
    RECOMMENDED_ACTIONS = {
        'direct': (
            "1. Draft cross-examination questions highlighting both statements\n"
            "2. Request clarification from the author\n"
            "3. File position statement citing the contradiction"
        ),
        'self': (
            "1. File position statement citing both statements with exact quotes\n"
            "2. Request a Lucas direction if credibility is in issue\n"
            "3. Prepare cross-examination on the specific inconsistency\n"
            "4. Consider inviting the court to make no finding based on this evidence"
        ),
        'modality': (
            "1. Submit that findings based on unproved allegations lack evidential foundation\n"
            "2. Cite Re B [2008] UKHL 35 at paragraphs 2 and 70\n"
            "3. Request the court treat the matter as unproved\n"
            "4. Invite the court to disregard in the welfare assessment"
        ),
        'temporal': (
            "1. Create detailed timeline exhibit showing the impossibility\n"
            "2. Request disclosure of documents that might clarify sequence\n"
            "3. Cross-examine on specific dates and times"
        ),
        'value': (
            "1. Request clarification in writing\n"
            "2. Seek independent evidence to verify\n"
            "3. Cross-examine on the discrepancy"
        ),
        'attribution': (
            "1. Request disclosure of any recordings\n"
            "2. Seek contemporaneous notes\n"
            "3. Cross-examine both parties on attribution"
        ),
    }
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize with semantic similarity model."""
        self.model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                logger.info(f"Loaded sentence-transformer model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")
    
    def detect_contradictions(
        self,
        claims,
        case_id: str
    ) -> List[ContradictionCandidate]:
        """
        Detect contradictions among a list of claims.

        Uses optimized blocking strategy:
        1. Pre-compute all embeddings in batch
        2. Compute similarity matrix efficiently
        3. Only analyze pairs above threshold

        Args:
            claims: QuerySet or list of Claim model instances
            case_id: Case identifier

        Returns:
            List of ContradictionCandidate objects
        """
        contradictions = []
        claims_list = list(claims)
        n = len(claims_list)

        if n < 2:
            return contradictions

        logger.info(f"Analyzing {n} claims for contradictions (optimized)...")

        # Pre-compute embeddings and similarity matrix
        embeddings = {}
        similarity_matrix = None

        if self.model and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                texts = [c.claim_text for c in claims_list]
                all_embeddings = self.model.encode(texts, convert_to_tensor=True)

                # Store embeddings for later use
                for i, claim in enumerate(claims_list):
                    embeddings[str(claim.id)] = all_embeddings[i]

                # Compute full similarity matrix at once (much faster than pairwise)
                similarity_matrix = util.cos_sim(all_embeddings, all_embeddings)

                # Find pairs above threshold using matrix operations
                # This is O(n²) in space but much faster due to vectorization
                if hasattr(torch, 'triu_indices'):
                    # Get upper triangle indices (excluding diagonal)
                    rows, cols = torch.triu_indices(n, n, offset=1)
                    similarities = similarity_matrix[rows, cols]

                    # Filter to pairs above threshold
                    mask = similarities >= self.SIMILARITY_THRESHOLD
                    candidate_pairs = list(zip(
                        rows[mask].tolist(),
                        cols[mask].tolist(),
                        similarities[mask].tolist()
                    ))

                    logger.info(f"Found {len(candidate_pairs)} candidate pairs above threshold")

                    # Analyze only candidate pairs
                    for i, j, sim in candidate_pairs:
                        claim_a = claims_list[i]
                        claim_b = claims_list[j]
                        candidate = self._analyze_pair(claim_a, claim_b, sim)
                        if candidate:
                            contradictions.append(candidate)

                    logger.info(f"Found {len(contradictions)} contradictions")
                    return contradictions
            except Exception as e:
                logger.warning(f"Optimized detection failed, falling back: {e}")
                similarity_matrix = None

        # Fallback: Use blocking by subject/author for efficiency
        # Group claims by subject for targeted comparison
        subject_blocks: Dict[str, List[int]] = {}
        author_blocks: Dict[str, List[int]] = {}

        for i, claim in enumerate(claims_list):
            # Block by subject
            if claim.subject:
                key = claim.subject.lower().strip()
                if key not in subject_blocks:
                    subject_blocks[key] = []
                subject_blocks[key].append(i)

            # Block by author (for self-contradiction detection)
            if claim.asserted_by:
                key = claim.asserted_by.lower().strip()
                if key not in author_blocks:
                    author_blocks[key] = []
                author_blocks[key].append(i)

        # Compare within subject blocks first (most likely contradictions)
        compared_pairs = set()

        for indices in subject_blocks.values():
            if len(indices) < 2:
                continue
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    idx_a, idx_b = indices[i], indices[j]
                    pair_key = (min(idx_a, idx_b), max(idx_a, idx_b))
                    if pair_key in compared_pairs:
                        continue
                    compared_pairs.add(pair_key)

                    claim_a, claim_b = claims_list[idx_a], claims_list[idx_b]
                    similarity = self._calculate_similarity(claim_a, claim_b, embeddings)

                    if similarity >= self.SIMILARITY_THRESHOLD:
                        candidate = self._analyze_pair(claim_a, claim_b, similarity)
                        if candidate:
                            contradictions.append(candidate)

        # Also check within author blocks (self-contradictions)
        for indices in author_blocks.values():
            if len(indices) < 2:
                continue
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    idx_a, idx_b = indices[i], indices[j]
                    pair_key = (min(idx_a, idx_b), max(idx_a, idx_b))
                    if pair_key in compared_pairs:
                        continue
                    compared_pairs.add(pair_key)

                    claim_a, claim_b = claims_list[idx_a], claims_list[idx_b]
                    similarity = self._calculate_similarity(claim_a, claim_b, embeddings)

                    if similarity >= self.SIMILARITY_THRESHOLD:
                        candidate = self._analyze_pair(claim_a, claim_b, similarity)
                        if candidate:
                            contradictions.append(candidate)

        logger.info(f"Found {len(contradictions)} contradictions (compared {len(compared_pairs)} pairs)")
        return contradictions
    
    def _calculate_similarity(
        self,
        claim_a,
        claim_b,
        embeddings: Dict[str, Any]
    ) -> float:
        """Calculate semantic similarity between claims."""
        if self.model and embeddings:
            emb_a = embeddings.get(str(claim_a.id))
            emb_b = embeddings.get(str(claim_b.id))
            if emb_a is not None and emb_b is not None:
                return float(util.cos_sim(emb_a, emb_b)[0][0])
        
        # Fallback: Jaccard similarity
        words_a = set(claim_a.claim_text.lower().split())
        words_b = set(claim_b.claim_text.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        return intersection / union if union > 0 else 0.0
    
    def _analyze_pair(
        self,
        claim_a,
        claim_b,
        similarity: float
    ) -> Optional[ContradictionCandidate]:
        """Analyze a pair of claims for contradictions."""
        
        # Check for same author
        same_author = (
            claim_a.asserted_by and claim_b.asserted_by and
            claim_a.asserted_by.lower().strip() == claim_b.asserted_by.lower().strip()
        )
        
        # 1. Self-contradiction with polarity difference
        if same_author and claim_a.polarity != claim_b.polarity:
            if self._subjects_match(claim_a, claim_b):
                return self._create_candidate(
                    claim_a, claim_b, 'self', 0.9, similarity, same_author
                )
        
        # 2. Direct contradiction via negation
        if self._check_negation_contradiction(claim_a, claim_b):
            ctype = 'self' if same_author else 'direct'
            return self._create_candidate(
                claim_a, claim_b, ctype, 0.85, similarity, same_author
            )
        
        # 3. Modality confusion
        if self._check_modality_confusion(claim_a, claim_b):
            return self._create_candidate(
                claim_a, claim_b, 'modality', 0.8, similarity, same_author
            )
        
        # 4. Temporal conflict
        if self._check_temporal_conflict(claim_a, claim_b):
            return self._create_candidate(
                claim_a, claim_b, 'temporal', 0.75, similarity, same_author, temporal_conflict=True
            )
        
        # 5. Value mismatch
        if self._check_value_mismatch(claim_a, claim_b):
            return self._create_candidate(
                claim_a, claim_b, 'value', 0.7, similarity, same_author
            )
        
        return None
    
    def _subjects_match(self, claim_a, claim_b) -> bool:
        """Check if claims are about the same subject."""
        if claim_a.subject and claim_b.subject:
            return claim_a.subject.lower().strip() == claim_b.subject.lower().strip()
        return False
    
    def _check_negation_contradiction(self, claim_a, claim_b) -> bool:
        """Check for direct contradiction via negation."""
        text_a = claim_a.claim_text.lower()
        text_b = claim_b.claim_text.lower()
        
        neg_a = any(re.search(p, text_a) for p in self.NEGATION_PATTERNS)
        neg_b = any(re.search(p, text_b) for p in self.NEGATION_PATTERNS)
        
        if neg_a != neg_b:
            if self._subjects_match(claim_a, claim_b):
                return True
        
        return False
    
    def _check_modality_confusion(self, claim_a, claim_b) -> bool:
        """Check for allegation treated as fact."""
        modalities = {claim_a.modality, claim_b.modality}
        
        if 'alleged' in modalities and 'asserted' in modalities:
            asserted = claim_a if claim_a.modality == 'asserted' else claim_b
            if asserted.certainty >= 0.7:
                return True
        
        return False
    
    def _check_temporal_conflict(self, claim_a, claim_b) -> bool:
        """Check for temporal impossibility."""
        if not (claim_a.time_start and claim_b.time_start):
            return False
        
        if self._subjects_match(claim_a, claim_b):
            if claim_a.time_start != claim_b.time_start:
                return True
        
        return False
    
    def _check_value_mismatch(self, claim_a, claim_b) -> bool:
        """Check for different values for same attribute."""
        if not (claim_a.object_value and claim_b.object_value):
            return False
        
        if (claim_a.subject and claim_b.subject and 
            claim_a.predicate and claim_b.predicate):
            if (claim_a.subject.lower() == claim_b.subject.lower() and
                claim_a.predicate.lower() == claim_b.predicate.lower()):
                if claim_a.object_value.lower() != claim_b.object_value.lower():
                    return True
        
        return False
    
    def _create_candidate(
        self,
        claim_a,
        claim_b,
        contradiction_type: str,
        confidence: float,
        similarity: float,
        same_author: bool,
        temporal_conflict: bool = False
    ) -> ContradictionCandidate:
        """Create a ContradictionCandidate with full details."""
        
        author_note = f" by {claim_a.asserted_by}" if same_author else ""
        
        descriptions = {
            'direct': f"Direct contradiction{author_note}: These claims make opposite assertions about the same subject.",
            'self': f"Self-contradiction: {claim_a.asserted_by} contradicts their own prior statement.",
            'modality': f"Modality confusion{author_note}: An allegation is treated as an established fact without proof.",
            'temporal': f"Temporal conflict{author_note}: These events cannot both be true given the stated timeline.",
            'value': f"Value mismatch{author_note}: Different values stated for the same attribute.",
            'attribution': f"Attribution conflict{author_note}: Conflicting accounts of who said or did what.",
        }
        
        return ContradictionCandidate(
            claim_a_id=claim_a.id,
            claim_b_id=claim_b.id,
            contradiction_type=contradiction_type,
            confidence=confidence,
            semantic_similarity=similarity,
            description=descriptions.get(contradiction_type, "Contradiction detected"),
            legal_significance=self.LEGAL_SIGNIFICANCE.get(contradiction_type),
            recommended_action=self.RECOMMENDED_ACTIONS.get(contradiction_type),
            temporal_conflict=temporal_conflict,
            same_author=same_author,
        )
    
    def save_contradictions(
        self,
        candidates: List[ContradictionCandidate],
        case,
        claims_by_id: Dict[str, Any]
    ) -> int:
        """
        Save contradiction candidates to the database.
        
        Args:
            candidates: List of ContradictionCandidate objects
            case: Case model instance
            claims_by_id: Dict mapping claim IDs to Claim instances
            
        Returns:
            Number of contradictions created
        """
        from django_backend.analysis.models import Contradiction, Severity
        
        created_count = 0
        
        with transaction.atomic():
            for candidate in candidates:
                claim_a = claims_by_id.get(str(candidate.claim_a_id))
                claim_b = claims_by_id.get(str(candidate.claim_b_id))
                
                if not claim_a or not claim_b:
                    continue
                
                # Check for existing
                exists = Contradiction.objects.filter(
                    case=case,
                    claim_a=claim_a,
                    claim_b=claim_b
                ).exists() or Contradiction.objects.filter(
                    case=case,
                    claim_a=claim_b,
                    claim_b=claim_a
                ).exists()
                
                if exists:
                    continue
                
                Contradiction.objects.create(
                    case=case,
                    contradiction_type=candidate.contradiction_type,
                    severity=self._confidence_to_severity(candidate.confidence),
                    claim_a=claim_a,
                    claim_b=claim_b,
                    description=candidate.description,
                    legal_significance=candidate.legal_significance,
                    recommended_action=candidate.recommended_action,
                    confidence=candidate.confidence,
                    semantic_similarity=candidate.semantic_similarity,
                    temporal_conflict=candidate.temporal_conflict,
                    same_author=candidate.same_author,
                )
                created_count += 1
        
        return created_count
    
    def _confidence_to_severity(self, confidence: float) -> str:
        """Map confidence to severity level."""
        if confidence >= 0.9:
            return 'critical'
        elif confidence >= 0.8:
            return 'high'
        elif confidence >= 0.6:
            return 'medium'
        else:
            return 'low'

