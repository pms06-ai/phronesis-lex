"""
FCIP v5.0 Argumentation Engine

Builds Toulmin argument structures with substantive legal rule warrants.

Legal Rules Library:
- CA1989 s1(1) Paramountcy Principle
- CA1989 s1(3) Welfare Checklist
- CA1989 s31(2) Threshold Criteria
- FPR 2010 procedural rules
- PD12J Domestic Abuse
- Re B standard of proof
- Re W Lucas direction
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..models.core import ToulminArgument, Claim, Confidence


# =============================================================================
# LEGAL RULES LIBRARY
# =============================================================================

@dataclass(frozen=True)
class LegalRule:
    """A substantive legal rule for argument warrants."""
    rule_id: str
    short_name: str
    full_citation: str
    text: str
    category: str  # welfare, threshold, evidence, professional, procedural


LEGAL_RULES: Dict[str, LegalRule] = {
    # Children Act 1989
    "CA1989.s1.1": LegalRule(
        "CA1989.s1.1",
        "Paramountcy Principle",
        "Children Act 1989, Section 1(1)",
        "When a court determines any question with respect to the upbringing of a child, "
        "the child's welfare shall be the court's paramount consideration.",
        "welfare"
    ),
    "CA1989.s1.2": LegalRule(
        "CA1989.s1.2",
        "No Delay Principle",
        "Children Act 1989, Section 1(2)",
        "In any proceedings in which any question with respect to the upbringing of a child arises, "
        "the court shall have regard to the general principle that any delay in determining the "
        "question is likely to prejudice the welfare of the child.",
        "welfare"
    ),
    "CA1989.s1.3": LegalRule(
        "CA1989.s1.3",
        "Welfare Checklist",
        "Children Act 1989, Section 1(3)",
        "A court shall have regard in particular to: (a) the ascertainable wishes and feelings of "
        "the child; (b) physical, emotional and educational needs; (c) likely effect of any change; "
        "(d) age, sex, background; (e) any harm suffered or at risk of suffering; "
        "(f) capability of parents; (g) range of powers available.",
        "welfare"
    ),
    "CA1989.s31.2": LegalRule(
        "CA1989.s31.2",
        "Threshold Criteria",
        "Children Act 1989, Section 31(2)",
        "A court may only make a care order or supervision order if it is satisfied: "
        "(a) that the child is suffering, or is likely to suffer, significant harm; and "
        "(b) that the harm is attributable to the care given to the child, or likely to be given "
        "if the order were not made, not being what it would be reasonable to expect a parent to give.",
        "threshold"
    ),

    # Practice Directions
    "PD12J": LegalRule(
        "PD12J",
        "Domestic Abuse PD",
        "Practice Direction 12J FPR 2010",
        "The court must at all stages of the proceedings consider whether domestic abuse is raised "
        "as an issue; and if so, must identify at the earliest opportunity the factual and welfare "
        "issues involved and consider the nature of any allegation.",
        "welfare"
    ),
    "PD12B": LegalRule(
        "PD12B",
        "Child Arrangements Programme",
        "Practice Direction 12B FPR 2010",
        "The Child Arrangements Programme applies to all private law proceedings under the "
        "Children Act 1989 and sets out the approach to be taken by the court.",
        "procedural"
    ),

    # Case Law
    "Re_B_2008": LegalRule(
        "Re_B_2008",
        "Re B Standard",
        "Re B [2008] UKHL 35",
        "The standard of proof in care proceedings is the balance of probabilities. "
        "There is no room for a finding that threshold is crossed on the basis that there is "
        "a 'real possibility' that the child was harmed. Unproved facts must be left out entirely.",
        "evidence"
    ),
    "Re_W_Lucas": LegalRule(
        "Re_W_Lucas",
        "Lucas Direction",
        "R v Lucas [1981] QB 720; Re H-C [2016] EWCA Civ 136",
        "A person may lie for many reasons. The fact that a person has lied about one matter "
        "does not mean they have lied about everything. A lie is only probative of guilt if it "
        "is told to conceal the truth about the matter in issue.",
        "evidence"
    ),
    "Re_A_2015": LegalRule(
        "Re_A_2015",
        "Re A (A Child)",
        "Re A (A Child) [2015] EWFC 11",
        "Evidence cannot be evaluated in separate compartments. The court must take account of "
        "all the evidence and consider each piece of evidence in the context of all the other evidence.",
        "evidence"
    ),

    # Professional Standards
    "FJC_Guidance": LegalRule(
        "FJC_Guidance",
        "Expert Witness Guidance",
        "FJC Guidelines for Expert Witnesses in Family Proceedings",
        "Experts must be objective and independent. They must distinguish clearly between fact "
        "and opinion. They must acknowledge the limitations of their expertise and methodology.",
        "professional"
    ),
    "SRA_Code": LegalRule(
        "SRA_Code",
        "SRA Code of Conduct",
        "SRA Standards and Regulations",
        "Solicitors must act in the best interests of each client. They must act with honesty "
        "and integrity. They must not mislead or attempt to mislead the court.",
        "professional"
    ),
    "BSB_Handbook": LegalRule(
        "BSB_Handbook",
        "BSB Handbook",
        "Bar Standards Board Handbook",
        "Barristers must not knowingly or recklessly mislead the court. They owe a duty to the "
        "court to ensure the proper administration of justice.",
        "professional"
    ),
}


# =============================================================================
# ARGUMENT PATTERNS
# =============================================================================

class ArgumentPattern(str, Enum):
    """Common argument patterns in family proceedings."""
    WELFARE_ASSESSMENT = "welfare_assessment"
    THRESHOLD_SATISFIED = "threshold_satisfied"
    THRESHOLD_NOT_SATISFIED = "threshold_not_satisfied"
    CREDIBILITY_FINDING = "credibility_finding"
    EXPERT_OPINION = "expert_opinion"
    PROCEDURAL_BREACH = "procedural_breach"
    BIAS_FINDING = "bias_finding"


ARGUMENT_TEMPLATES: Dict[ArgumentPattern, Dict] = {
    ArgumentPattern.WELFARE_ASSESSMENT: {
        "rules": ["CA1989.s1.1", "CA1989.s1.3"],
        "qualifiers": ["on balance", "in light of the welfare checklist"],
        "rebuttals": [
            "Unless welfare factors are weighed differently",
            "Unless the child's wishes carry greater weight",
            "Unless previously unknown evidence emerges"
        ],
        "falsifiability_types": [
            "missing_evidence",
            "alternative_interpretation",
            "timeline_conflict"
        ]
    },
    ArgumentPattern.THRESHOLD_SATISFIED: {
        "rules": ["CA1989.s31.2", "Re_B_2008"],
        "qualifiers": ["on the balance of probabilities"],
        "rebuttals": [
            "Unless harm cannot be proved to civil standard",
            "Unless harm is not attributable to parental care",
            "Unless reasonable parenting standard is met"
        ],
        "falsifiability_types": [
            "evidence_gap",
            "alternative_explanation",
            "attribution_dispute"
        ]
    },
    ArgumentPattern.CREDIBILITY_FINDING: {
        "rules": ["Re_W_Lucas", "Re_A_2015"],
        "qualifiers": ["having considered all the evidence"],
        "rebuttals": [
            "Unless lies were for different reasons (Lucas direction)",
            "Unless corroborating evidence contradicts finding",
            "Unless evidence was considered in isolation"
        ],
        "falsifiability_types": [
            "corroborating_evidence",
            "motivation_analysis",
            "consistency_check"
        ]
    },
    ArgumentPattern.EXPERT_OPINION: {
        "rules": ["FJC_Guidance"],
        "qualifiers": ["subject to expert limitations"],
        "rebuttals": [
            "Unless expert exceeded their expertise",
            "Unless methodology is flawed",
            "Unless contrary expert evidence exists"
        ],
        "falsifiability_types": [
            "methodology_critique",
            "expertise_scope",
            "conflicting_opinion"
        ]
    },
    ArgumentPattern.BIAS_FINDING: {
        "rules": ["Re_A_2015", "FJC_Guidance"],
        "qualifiers": ["the evidence suggests"],
        "rebuttals": [
            "Unless bias pattern is within normal range",
            "Unless statistical analysis is flawed",
            "Unless contextual factors explain variance"
        ],
        "falsifiability_types": [
            "statistical_reanalysis",
            "baseline_comparison",
            "contextual_review"
        ]
    },
}


# =============================================================================
# ARGUMENTATION ENGINE
# =============================================================================

class ArgumentationEngine:
    """Engine for building Toulmin arguments with legal warrants."""

    def __init__(self, rules: Optional[Dict[str, LegalRule]] = None):
        self.rules = rules or LEGAL_RULES
        self.templates = ARGUMENT_TEMPLATES

    def build_argument(
        self,
        claim_text: str,
        supporting_claims: List[Claim],
        pattern: ArgumentPattern,
        case_id: str
    ) -> ToulminArgument:
        """
        Build a Toulmin argument structure.

        Args:
            claim_text: The main claim/conclusion
            supporting_claims: Claims providing grounds
            pattern: The argument pattern to use
            case_id: The case identifier

        Returns:
            A complete ToulminArgument
        """
        template = self.templates.get(pattern, self.templates[ArgumentPattern.WELFARE_ASSESSMENT])

        # Get primary rule for warrant
        rule_id = template["rules"][0]
        rule = self.rules[rule_id]

        # Build grounds from supporting claims
        grounds = [
            f"[{c.claim_type.value}] {c.text[:200]}... (certainty: {c.certainty:.2f})"
            for c in supporting_claims[:5]  # Limit to 5 key claims
        ]

        # Build backing from all rules
        backing = [self.rules[rid].full_citation for rid in template["rules"] if rid in self.rules]

        # Generate falsifiability conditions
        falsifiability_conditions = self._generate_falsifiability(
            claim_text,
            supporting_claims,
            template["falsifiability_types"]
        )

        # Calculate confidence bounds
        if supporting_claims:
            confidences = [c.certainty for c in supporting_claims]
            conf_mean = sum(confidences) / len(confidences)
            conf_lower = min(confidences) * 0.9  # 10% reduction for lower bound
            conf_upper = min(1.0, max(confidences) * 1.05)  # 5% increase for upper bound
        else:
            conf_mean, conf_lower, conf_upper = 0.5, 0.3, 0.7

        return ToulminArgument(
            case_id=case_id,
            claim_text=claim_text,
            grounds=grounds,
            warrant=f"Under {rule.short_name}: {rule.text[:200]}...",
            warrant_rule_id=rule_id,
            backing=backing,
            qualifier=template["qualifiers"][0],
            rebuttal=template["rebuttals"],
            falsifiability_conditions=falsifiability_conditions,
            missing_evidence=self._identify_missing_evidence(supporting_claims),
            alternative_explanations=self._generate_alternatives(claim_text, pattern),
            confidence_lower=conf_lower,
            confidence_upper=conf_upper,
            confidence_mean=conf_mean
        )

    def _generate_falsifiability(
        self,
        claim: str,
        supporting_claims: List[Claim],
        types: List[str]
    ) -> List[dict]:
        """Generate falsifiability conditions."""
        conditions = []

        for ftype in types:
            if ftype == "missing_evidence":
                conditions.append({
                    "type": "missing_evidence",
                    "description": "Documentation exists that contradicts or qualifies the claim",
                    "test_query": f"Search for documents that contradict: {claim[:50]}...",
                    "impact": "Would weaken or invalidate the argument",
                    "priority": 1
                })
            elif ftype == "timeline_conflict":
                conditions.append({
                    "type": "timeline_conflict",
                    "description": "Events occurred in different order than claimed",
                    "test_query": "Verify temporal sequence of cited events",
                    "impact": "Would undermine causal reasoning",
                    "priority": 2
                })
            elif ftype == "alternative_explanation":
                conditions.append({
                    "type": "alternative_explanation",
                    "description": "An equally plausible alternative explanation exists",
                    "test_query": "Consider alternative interpretations of evidence",
                    "impact": "Would reduce confidence in conclusion",
                    "priority": 2
                })
            elif ftype == "evidence_gap":
                conditions.append({
                    "type": "evidence_gap",
                    "description": "Critical evidence is missing or unavailable",
                    "test_query": "Identify expected documents not in disclosure",
                    "impact": "Would indicate incomplete analysis",
                    "priority": 1
                })

        return conditions

    def _identify_missing_evidence(self, claims: List[Claim]) -> List[str]:
        """Identify potentially missing evidence."""
        missing = []

        # Check for low-confidence claims
        low_conf = [c for c in claims if c.certainty < 0.5]
        if low_conf:
            missing.append(f"{len(low_conf)} claims have low confidence and may need additional support")

        # Check for allegations without corroboration
        allegations = [c for c in claims if c.claim_type.value == "allegation"]
        if allegations:
            missing.append(f"{len(allegations)} allegations may require corroborating evidence")

        return missing

    def _generate_alternatives(self, claim: str, pattern: ArgumentPattern) -> List[str]:
        """Generate alternative explanations."""
        alternatives = []

        if pattern == ArgumentPattern.WELFARE_ASSESSMENT:
            alternatives = [
                "Alternative weighting of welfare factors could lead to different conclusion",
                "Child's wishes may not have been fully ascertained or understood"
            ]
        elif pattern == ArgumentPattern.THRESHOLD_SATISFIED:
            alternatives = [
                "Harm may be attributable to factors other than parental care",
                "Standard of care may be reasonable given circumstances"
            ]
        elif pattern == ArgumentPattern.CREDIBILITY_FINDING:
            alternatives = [
                "Inconsistencies may be due to trauma or passage of time",
                "Witness may have lied to protect others, not about core facts"
            ]

        return alternatives

    def get_rule(self, rule_id: str) -> Optional[LegalRule]:
        """Get a legal rule by ID."""
        return self.rules.get(rule_id)

    def get_rules_by_category(self, category: str) -> List[LegalRule]:
        """Get all rules in a category."""
        return [r for r in self.rules.values() if r.category == category]

    def build_arguments_from_findings(
        self,
        findings: List[dict],
        claims: List[Claim],
        case_id: str
    ) -> List[ToulminArgument]:
        """
        Build arguments from a list of findings.

        Args:
            findings: List of finding dicts with 'type' and 'summary'
            claims: List of claims to use as grounds
            case_id: The case identifier

        Returns:
            List of ToulminArguments
        """
        arguments = []

        for finding in findings:
            finding_type = finding.get("type", "")
            summary = finding.get("summary", "")

            # Map finding type to argument pattern
            pattern = self._map_finding_to_pattern(finding_type)

            # Find relevant supporting claims
            supporting = self._find_supporting_claims(finding, claims)

            if supporting:
                arg = self.build_argument(summary, supporting, pattern, case_id)
                arguments.append(arg)

        return arguments

    def _map_finding_to_pattern(self, finding_type: str) -> ArgumentPattern:
        """Map finding type to argument pattern."""
        mapping = {
            "welfare": ArgumentPattern.WELFARE_ASSESSMENT,
            "threshold": ArgumentPattern.THRESHOLD_SATISFIED,
            "credibility": ArgumentPattern.CREDIBILITY_FINDING,
            "expert": ArgumentPattern.EXPERT_OPINION,
            "bias": ArgumentPattern.BIAS_FINDING,
            "procedural": ArgumentPattern.PROCEDURAL_BREACH,
        }
        return mapping.get(finding_type.lower(), ArgumentPattern.WELFARE_ASSESSMENT)

    def _find_supporting_claims(self, finding: dict, claims: List[Claim]) -> List[Claim]:
        """Find claims that support a finding."""
        # Simple keyword matching - could be enhanced with semantic similarity
        keywords = finding.get("summary", "").lower().split()[:5]
        supporting = []

        for claim in claims:
            claim_text = claim.text.lower()
            matches = sum(1 for kw in keywords if kw in claim_text)
            if matches >= 2:  # At least 2 keyword matches
                supporting.append(claim)

        return supporting[:5]  # Return top 5
