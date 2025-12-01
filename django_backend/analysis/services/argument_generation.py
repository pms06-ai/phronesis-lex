"""
Argument Generation Service
Builds Toulmin-structured legal arguments from claims and evidence.
"""
import logging
from typing import List, Optional, Dict, Any
from enum import Enum

from django.db import transaction

logger = logging.getLogger(__name__)


class ArgumentPattern(str, Enum):
    """Common argument patterns in family proceedings."""
    WELFARE_ASSESSMENT = "welfare_assessment"
    THRESHOLD_SATISFIED = "threshold_satisfied"
    THRESHOLD_NOT_SATISFIED = "threshold_not_satisfied"
    CREDIBILITY_FINDING = "credibility_finding"
    EXPERT_OPINION = "expert_opinion"
    PROCEDURAL_BREACH = "procedural_breach"
    BIAS_FINDING = "bias_finding"


# Argument templates with UK Family Law warrants
ARGUMENT_TEMPLATES = {
    ArgumentPattern.WELFARE_ASSESSMENT: {
        "rules": ["CA1989.s1.1", "CA1989.s1.3"],
        "qualifiers": ["on balance", "having regard to the welfare checklist"],
        "rebuttals": [
            "Unless welfare factors are weighed differently by the court",
            "Unless the child's expressed wishes carry greater weight",
            "Unless previously unknown evidence emerges"
        ],
        "falsifiability_types": [
            {"type": "missing_evidence", "description": "Evidence exists that contradicts welfare analysis"},
            {"type": "alternative_interpretation", "description": "Welfare factors could be weighed differently"},
            {"type": "child_wishes", "description": "Child's wishes not fully ascertained"}
        ]
    },
    ArgumentPattern.THRESHOLD_SATISFIED: {
        "rules": ["CA1989.s31.2", "Re_B_2008"],
        "qualifiers": ["on the balance of probabilities"],
        "rebuttals": [
            "Unless harm cannot be proved to the civil standard (Re B)",
            "Unless harm is not attributable to parental care",
            "Unless reasonable parenting standard was met in the circumstances"
        ],
        "falsifiability_types": [
            {"type": "evidence_gap", "description": "Evidence of harm is absent or insufficient"},
            {"type": "alternative_attribution", "description": "Harm attributable to other factors"},
            {"type": "reasonable_care", "description": "Care was reasonable given circumstances"}
        ]
    },
    ArgumentPattern.CREDIBILITY_FINDING: {
        "rules": ["Re_W_Lucas", "Re_A_2015"],
        "qualifiers": ["having considered all the evidence holistically"],
        "rebuttals": [
            "Unless lies were for reasons other than concealment (Lucas direction)",
            "Unless corroborating evidence contradicts this finding",
            "Unless evidence was assessed in isolation contrary to Re A"
        ],
        "falsifiability_types": [
            {"type": "lucas_analysis", "description": "Reason for lie not properly analysed"},
            {"type": "corroboration", "description": "Independent evidence contradicts finding"},
            {"type": "compartmentalisation", "description": "Evidence not assessed holistically"}
        ]
    },
    ArgumentPattern.EXPERT_OPINION: {
        "rules": ["FJC_Guidance", "PD25C"],
        "qualifiers": ["subject to the court's own assessment"],
        "rebuttals": [
            "Unless the expert exceeded the scope of their expertise",
            "Unless methodology was flawed or inappropriate",
            "Unless contrary expert evidence should be preferred"
        ],
        "falsifiability_types": [
            {"type": "expertise_scope", "description": "Expert opined outside their field"},
            {"type": "methodology", "description": "Methodology was inappropriate"},
            {"type": "contrary_evidence", "description": "Contrary expert evidence exists"}
        ]
    },
    ArgumentPattern.BIAS_FINDING: {
        "rules": ["Re_A_2015", "FJC_Guidance", "SWCCF"],
        "qualifiers": ["the statistical analysis suggests"],
        "rebuttals": [
            "Unless bias pattern is within normal range for document type",
            "Unless statistical analysis methodology is challenged",
            "Unless contextual factors adequately explain the variance"
        ],
        "falsifiability_types": [
            {"type": "statistical_challenge", "description": "Baseline or methodology disputed"},
            {"type": "contextual_explanation", "description": "Variance explained by case context"},
            {"type": "professional_justification", "description": "Professional justifies language used"}
        ]
    },
}


class ArgumentGenerationService:
    """
    Service for generating Toulmin-structured legal arguments.
    
    Builds arguments from claims with legal rule warrants,
    falsifiability conditions, and confidence bounds.
    """
    
    def __init__(self):
        self.rules = {}
        self._load_rules()
    
    def _load_rules(self):
        """Load legal rules from database."""
        from django_backend.analysis.models import LegalRule
        
        try:
            for rule in LegalRule.objects.all():
                self.rules[rule.rule_id] = {
                    'short_name': rule.short_name,
                    'full_citation': rule.full_citation,
                    'text': rule.text,
                    'category': rule.category,
                }
        except Exception as e:
            logger.warning(f"Could not load legal rules: {e}")
    
    def generate_argument(
        self,
        claim_text: str,
        supporting_claims: List[Any],
        pattern: ArgumentPattern,
        case
    ) -> Dict[str, Any]:
        """
        Generate a Toulmin argument from claims.
        
        Args:
            claim_text: The main conclusion
            supporting_claims: Claims supporting the argument
            pattern: The argument pattern to use
            case: Case model instance
            
        Returns:
            Dict with argument structure
        """
        template = ARGUMENT_TEMPLATES.get(pattern, ARGUMENT_TEMPLATES[ArgumentPattern.WELFARE_ASSESSMENT])
        
        # Get primary rule
        rule_id = template["rules"][0]
        rule = self.rules.get(rule_id, {})
        
        # Build grounds from claims
        grounds = []
        for claim in supporting_claims[:5]:
            certainty = getattr(claim, 'certainty', 0.5)
            grounds.append(
                f"[{claim.claim_type}] {claim.claim_text[:200]}... (certainty: {certainty:.2f})"
            )
        
        # Build backing from all rules
        backing = []
        for rid in template["rules"]:
            r = self.rules.get(rid)
            if r:
                backing.append(r['full_citation'])
        
        # Calculate confidence bounds
        if supporting_claims:
            confidences = [getattr(c, 'certainty', 0.5) for c in supporting_claims]
            conf_mean = sum(confidences) / len(confidences)
            conf_lower = min(confidences) * 0.9
            conf_upper = min(1.0, max(confidences) * 1.05)
        else:
            conf_mean, conf_lower, conf_upper = 0.5, 0.3, 0.7
        
        # Build warrant
        warrant = f"Under {rule.get('short_name', 'applicable law')}: {rule.get('text', 'Legal rule applies.')[:300]}..."
        
        # Missing evidence
        missing_evidence = []
        low_conf = [c for c in supporting_claims if getattr(c, 'certainty', 0.5) < 0.5]
        if low_conf:
            missing_evidence.append(f"{len(low_conf)} supporting claims have low confidence")
        
        allegations = [c for c in supporting_claims if getattr(c, 'claim_type', '') == 'allegation']
        if allegations:
            missing_evidence.append(f"{len(allegations)} allegations may require corroboration")
        
        # Alternative explanations
        alternatives = self._generate_alternatives(claim_text, pattern)
        
        return {
            'claim_text': claim_text,
            'grounds': grounds,
            'warrant': warrant,
            'warrant_rule_id': rule_id,
            'backing': backing,
            'qualifier': template['qualifiers'][0],
            'rebuttal': template['rebuttals'],
            'falsifiability_conditions': template['falsifiability_types'],
            'missing_evidence': missing_evidence,
            'alternative_explanations': alternatives,
            'confidence_lower': conf_lower,
            'confidence_upper': conf_upper,
            'confidence_mean': conf_mean,
        }
    
    def _generate_alternatives(self, claim: str, pattern: ArgumentPattern) -> List[str]:
        """Generate alternative explanations based on pattern."""
        alternatives = {
            ArgumentPattern.WELFARE_ASSESSMENT: [
                "Alternative weighting of welfare factors could support different outcome",
                "Child's wishes may not have been fully ascertained or understood"
            ],
            ArgumentPattern.THRESHOLD_SATISFIED: [
                "Harm may be attributable to factors other than parental care",
                "Care may have been reasonable given the specific circumstances"
            ],
            ArgumentPattern.CREDIBILITY_FINDING: [
                "Inconsistencies may be due to trauma or passage of time",
                "Witness may have been dishonest to protect others, not about core facts"
            ],
            ArgumentPattern.BIAS_FINDING: [
                "Language variance may be explained by case-specific factors",
                "Professional may have specific reasons for language choices"
            ],
        }
        return alternatives.get(pattern, ["Alternative interpretation of evidence is possible"])
    
    def save_argument(
        self,
        argument_data: Dict[str, Any],
        case,
        supporting_claims: List[Any] = None
    ):
        """Save generated argument to database."""
        from django_backend.analysis.models import ToulminArgument, LegalRule
        
        with transaction.atomic():
            warrant_rule = None
            if argument_data.get('warrant_rule_id'):
                try:
                    warrant_rule = LegalRule.objects.get(rule_id=argument_data['warrant_rule_id'])
                except LegalRule.DoesNotExist:
                    pass
            
            argument = ToulminArgument.objects.create(
                case=case,
                claim_text=argument_data['claim_text'],
                grounds=argument_data['grounds'],
                warrant=argument_data['warrant'],
                warrant_rule=warrant_rule,
                backing=argument_data['backing'],
                qualifier=argument_data['qualifier'],
                rebuttal=argument_data['rebuttal'],
                falsifiability_conditions=argument_data['falsifiability_conditions'],
                missing_evidence=argument_data['missing_evidence'],
                alternative_explanations=argument_data['alternative_explanations'],
                confidence_lower=argument_data['confidence_lower'],
                confidence_upper=argument_data['confidence_upper'],
                confidence_mean=argument_data['confidence_mean'],
            )
            
            if supporting_claims:
                argument.supporting_claims.set(supporting_claims[:5])
            
            return argument

