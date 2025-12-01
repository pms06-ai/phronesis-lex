"""
Professional Accountability Tracker

Tracks every professional involved in the case, their claims, contradictions,
bias indicators, and accountability issues.

This is the core of the accountability system - systematically documenting
exactly what each professional said, when, and how it contradicts other evidence.
"""

import sqlite3
import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict
from enum import Enum


class ProfessionalRole(Enum):
    POLICE_OFFICER = "police_officer"
    SOCIAL_WORKER = "social_worker"
    CAFCASS_OFFICER = "cafcass_officer"
    JUDGE = "judge"
    EXPERT = "expert"
    LOCAL_AUTHORITY = "local_authority"
    SOLICITOR = "solicitor"
    WITNESS = "witness"
    PARTY = "party"
    UNKNOWN = "unknown"


@dataclass
class ProfessionalProfile:
    """Complete profile of a professional in the case."""
    name: str
    normalized_name: str
    role: ProfessionalRole
    organization: Optional[str]
    
    # Claims made by this professional
    claims: List[dict] = field(default_factory=list)
    
    # Self-contradictions
    self_contradictions: List[dict] = field(default_factory=list)
    
    # Contradictions with others
    contradictions_with_others: List[dict] = field(default_factory=list)
    
    # Bias indicators
    bias_indicators: List[dict] = field(default_factory=list)
    
    # Documents authored/contributed to
    documents: List[str] = field(default_factory=list)
    
    # Key quotes
    key_quotes: List[dict] = field(default_factory=list)
    
    # Accountability score (higher = more issues)
    accountability_score: float = 0.0
    
    # Complaint routes
    complaint_routes: List[str] = field(default_factory=list)


class ProfessionalAccountabilityTracker:
    """
    Tracks and analyzes all professionals involved in the case.
    """
    
    # Known professionals and their roles
    KNOWN_PROFESSIONALS = {
        # Police
        'dci katie dounias': (ProfessionalRole.POLICE_OFFICER, 'Beds, Cambs & Herts Major Crime Unit'),
        'dc 2072 atkinson': (ProfessionalRole.POLICE_OFFICER, 'Cambridgeshire Constabulary'),
        'dc atkinson': (ProfessionalRole.POLICE_OFFICER, 'Cambridgeshire Constabulary'),
        'claire atkinson': (ProfessionalRole.POLICE_OFFICER, 'Cambridgeshire Constabulary'),
        
        # Social Workers
        'paul duggan': (ProfessionalRole.SOCIAL_WORKER, 'Cambridgeshire County Council'),
        'lucy ardern': (ProfessionalRole.SOCIAL_WORKER, 'Cambridgeshire County Council'),
        'sreenadh puthanpurakkal': (ProfessionalRole.SOCIAL_WORKER, 'Cambridgeshire County Council'),
        'butler': (ProfessionalRole.SOCIAL_WORKER, 'Cambridgeshire County Council'),
        
        # CAFCASS
        'guardian': (ProfessionalRole.CAFCASS_OFFICER, 'CAFCASS'),
        'children\'s guardian': (ProfessionalRole.CAFCASS_OFFICER, 'CAFCASS'),
        'cafcass': (ProfessionalRole.CAFCASS_OFFICER, 'CAFCASS'),
        
        # Judges
        'hhj gordon-saker': (ProfessionalRole.JUDGE, 'Family Court Peterborough'),
        'gordon-saker': (ProfessionalRole.JUDGE, 'Family Court Peterborough'),
        'the court': (ProfessionalRole.JUDGE, 'Family Court'),
        
        # Experts
        'dr vivien wong-spracklen': (ProfessionalRole.EXPERT, 'Psychology'),
        
        # Parties
        'samantha stephen': (ProfessionalRole.PARTY, 'Mother/Respondent'),
        'paul stephen': (ProfessionalRole.PARTY, 'Father/Respondent'),
        'mandy seamark': (ProfessionalRole.PARTY, 'Paternal Grandmother'),
        'mandy jane seamark': (ProfessionalRole.PARTY, 'Paternal Grandmother'),
        
        # Local Authority
        'local authority': (ProfessionalRole.LOCAL_AUTHORITY, 'Cambridgeshire County Council'),
        'cambridgeshire county council': (ProfessionalRole.LOCAL_AUTHORITY, 'Cambridgeshire County Council'),
    }
    
    # Bias indicators to search for
    BIAS_PATTERNS = {
        'certainty_language': [
            r'\bclearly\b', r'\bobviously\b', r'\bundoubtedly\b', r'\bcertainly\b',
            r'\bwithout doubt\b', r'\bno question\b', r'\bdefinitely\b'
        ],
        'negative_attribution': [
            r'\bfailed to\b', r'\brefused to\b', r'\bdeliberately\b', r'\bwilfully\b',
            r'\bchose not to\b', r'\bintentionally\b'
        ],
        'extreme_quantifiers': [
            r'\balways\b', r'\bnever\b', r'\bcompletely\b', r'\btotally\b',
            r'\babsolutely\b', r'\bentirely\b'
        ],
        'emotional_language': [
            r'\bshocking\b', r'\bappalling\b', r'\bdisturbing\b', r'\balarming\b',
            r'\bconcerning\b', r'\bworrying\b'
        ],
        'dismissive_language': [
            r'\bclaims\b', r'\balleges\b', r'\bpurports\b', r'\bso-called\b',
            r'\bsupposedly\b'
        ]
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.professionals: Dict[str, ProfessionalProfile] = {}
        
    def analyze_all_professionals(self) -> Dict[str, ProfessionalProfile]:
        """Analyze all professionals and build their profiles."""
        
        print("Analyzing professionals...")
        
        # Load all claims
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.*, d.filename, d.title, d.document_category
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
        """)
        claims = [dict(row) for row in cursor.fetchall()]
        
        print(f"  Loaded {len(claims)} claims")
        
        # Group claims by author
        claims_by_author = defaultdict(list)
        for claim in claims:
            author = claim.get('asserted_by')
            if author:
                normalized = self._normalize_name(author)
                claims_by_author[normalized].append(claim)
        
        print(f"  Found {len(claims_by_author)} unique authors")
        
        # Build profiles for each author
        for normalized_name, author_claims in claims_by_author.items():
            # Determine role and organization
            role, org = self._identify_role(normalized_name)
            
            profile = ProfessionalProfile(
                name=author_claims[0].get('asserted_by', normalized_name),
                normalized_name=normalized_name,
                role=role,
                organization=org,
                claims=author_claims
            )
            
            # Analyze bias in claims
            self._analyze_bias(profile)
            
            # Find self-contradictions
            self._find_self_contradictions(profile)
            
            # Collect documents
            docs = set()
            for claim in author_claims:
                doc = claim.get('filename') or claim.get('title')
                if doc:
                    docs.add(doc)
            profile.documents = list(docs)
            
            # Extract key quotes
            self._extract_key_quotes(profile)
            
            # Calculate accountability score
            self._calculate_accountability_score(profile)
            
            # Determine complaint routes
            self._determine_complaint_routes(profile)
            
            self.professionals[normalized_name] = profile
        
        # Find contradictions between professionals
        self._find_inter_professional_contradictions()
        
        return self.professionals
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a name for matching."""
        if not name:
            return "unknown"
        
        name = name.lower().strip()
        
        # Remove common suffixes
        name = re.sub(r'\s*\(.*?\)\s*', '', name)
        name = re.sub(r'\s*-\s*', ' ', name)
        
        # Standardize known variations
        variations = {
            'sw': 'social worker',
            'scw': 'social worker',
            'la': 'local authority',
            'cg': 'guardian',
            'fca': 'cafcass',
        }
        
        for abbrev, full in variations.items():
            if name.endswith(f' ({abbrev})') or name.endswith(f' {abbrev}'):
                name = name.replace(f' ({abbrev})', '').replace(f' {abbrev}', '')
        
        return name.strip()
    
    def _identify_role(self, normalized_name: str) -> Tuple[ProfessionalRole, Optional[str]]:
        """Identify the role and organization of a professional."""
        
        # Check known professionals
        for known_name, (role, org) in self.KNOWN_PROFESSIONALS.items():
            if known_name in normalized_name or normalized_name in known_name:
                return role, org
        
        # Infer from name patterns
        if 'social worker' in normalized_name or 'sw' in normalized_name:
            return ProfessionalRole.SOCIAL_WORKER, 'Unknown'
        if 'guardian' in normalized_name or 'cafcass' in normalized_name:
            return ProfessionalRole.CAFCASS_OFFICER, 'CAFCASS'
        if 'judge' in normalized_name or 'hhj' in normalized_name or 'recorder' in normalized_name:
            return ProfessionalRole.JUDGE, 'Family Court'
        if 'dc ' in normalized_name or 'dci ' in normalized_name or 'police' in normalized_name:
            return ProfessionalRole.POLICE_OFFICER, 'Police'
        if 'dr ' in normalized_name or 'professor' in normalized_name:
            return ProfessionalRole.EXPERT, 'Expert'
        if 'local authority' in normalized_name:
            return ProfessionalRole.LOCAL_AUTHORITY, 'Local Authority'
        if 'mother' in normalized_name or 'father' in normalized_name:
            return ProfessionalRole.PARTY, 'Party'
        
        return ProfessionalRole.UNKNOWN, None
    
    def _analyze_bias(self, profile: ProfessionalProfile):
        """Analyze bias indicators in a professional's claims."""
        
        for claim in profile.claims:
            text = claim.get('claim_text', '').lower()
            
            for bias_type, patterns in self.BIAS_PATTERNS.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        profile.bias_indicators.append({
                            'type': bias_type,
                            'pattern': pattern,
                            'matches': matches,
                            'claim_text': claim.get('claim_text'),
                            'document': claim.get('filename') or claim.get('title'),
                            'date': claim.get('date_made')
                        })
    
    def _find_self_contradictions(self, profile: ProfessionalProfile):
        """Find contradictions within a professional's own statements."""
        
        claims = profile.claims
        
        # Look for opposing statements
        for i, claim1 in enumerate(claims):
            text1 = (claim1.get('claim_text') or '').lower()
            
            for claim2 in claims[i+1:]:
                text2 = (claim2.get('claim_text') or '').lower()
                
                # Check for polarity opposites
                if self._are_contradictory(text1, text2):
                    profile.self_contradictions.append({
                        'claim_1': claim1.get('claim_text'),
                        'claim_2': claim2.get('claim_text'),
                        'doc_1': claim1.get('filename') or claim1.get('title'),
                        'doc_2': claim2.get('filename') or claim2.get('title'),
                        'date_1': claim1.get('date_made'),
                        'date_2': claim2.get('date_made')
                    })
    
    def _are_contradictory(self, text1: str, text2: str) -> bool:
        """Check if two texts are contradictory."""
        
        # Simple polarity check
        polarity_pairs = [
            ('did', 'did not'),
            ('was', 'was not'),
            ('has', 'has not'),
            ('is', 'is not'),
            ('can', 'cannot'),
            ('will', 'will not'),
            ('would', 'would not'),
            ('should', 'should not'),
            ('agreed', 'refused'),
            ('accepted', 'rejected'),
            ('true', 'false'),
            ('yes', 'no'),
        ]
        
        for pos, neg in polarity_pairs:
            if (pos in text1 and neg in text2) or (neg in text1 and pos in text2):
                # Check if they're about the same subject
                # (simplified - real implementation would use NLP)
                common_words = set(text1.split()) & set(text2.split())
                if len(common_words) > 5:  # Enough overlap to be same topic
                    return True
        
        return False
    
    def _extract_key_quotes(self, profile: ProfessionalProfile):
        """Extract the most significant quotes from a professional."""
        
        # Prioritize claims with bias indicators
        bias_claims = set()
        for bi in profile.bias_indicators:
            bias_claims.add(bi.get('claim_text'))
        
        # Prioritize claims from key documents
        key_doc_types = ['court_order', 'cafcass_report', 'social_work_report', 'expert_report', 'police_report']
        
        for claim in profile.claims:
            doc_type = claim.get('document_category', '')
            claim_text = claim.get('claim_text', '')
            
            # Add if it's from a key document or has bias
            if doc_type in key_doc_types or claim_text in bias_claims:
                profile.key_quotes.append({
                    'quote': claim_text,
                    'document': claim.get('filename') or claim.get('title'),
                    'date': claim.get('date_made'),
                    'doc_type': doc_type,
                    'has_bias': claim_text in bias_claims
                })
        
        # Limit to top 20
        profile.key_quotes = profile.key_quotes[:20]
    
    def _calculate_accountability_score(self, profile: ProfessionalProfile):
        """Calculate an accountability score for the professional."""
        
        score = 0.0
        
        # Points for self-contradictions (very significant)
        score += len(profile.self_contradictions) * 10
        
        # Points for bias indicators
        score += len(profile.bias_indicators) * 2
        
        # Points for contradictions with others (added later)
        score += len(profile.contradictions_with_others) * 5
        
        # Weight by role (professionals held to higher standard)
        role_weights = {
            ProfessionalRole.JUDGE: 2.0,
            ProfessionalRole.SOCIAL_WORKER: 1.5,
            ProfessionalRole.CAFCASS_OFFICER: 1.5,
            ProfessionalRole.POLICE_OFFICER: 1.5,
            ProfessionalRole.EXPERT: 1.5,
            ProfessionalRole.LOCAL_AUTHORITY: 1.3,
            ProfessionalRole.PARTY: 0.5,  # Lower weight for parties
            ProfessionalRole.UNKNOWN: 1.0,
        }
        
        score *= role_weights.get(profile.role, 1.0)
        
        profile.accountability_score = score
    
    def _determine_complaint_routes(self, profile: ProfessionalProfile):
        """Determine appropriate complaint routes for this professional."""
        
        routes = {
            ProfessionalRole.POLICE_OFFICER: ['IOPC', 'Police Professional Standards'],
            ProfessionalRole.SOCIAL_WORKER: ['HCPC Fitness to Practise', 'Employer', 'LGSCO'],
            ProfessionalRole.CAFCASS_OFFICER: ['CAFCASS Complaints', 'Parliamentary Ombudsman'],
            ProfessionalRole.JUDGE: ['JCIO (Judicial Conduct)', 'Appeal'],
            ProfessionalRole.LOCAL_AUTHORITY: ['LGSCO', 'Internal Complaints', 'Judicial Review'],
            ProfessionalRole.EXPERT: ['Professional Body', 'Court'],
        }
        
        profile.complaint_routes = routes.get(profile.role, ['Seek legal advice'])
    
    def _find_inter_professional_contradictions(self):
        """Find contradictions between different professionals."""
        
        professionals = list(self.professionals.values())
        
        for i, prof1 in enumerate(professionals):
            for prof2 in professionals[i+1:]:
                # Don't compare parties against each other (expected to disagree)
                if prof1.role == ProfessionalRole.PARTY and prof2.role == ProfessionalRole.PARTY:
                    continue
                
                # Compare claims
                for claim1 in prof1.claims[:50]:  # Limit for performance
                    text1 = (claim1.get('claim_text') or '').lower()
                    
                    for claim2 in prof2.claims[:50]:
                        text2 = (claim2.get('claim_text') or '').lower()
                        
                        if self._are_contradictory(text1, text2):
                            contradiction = {
                                'other_professional': prof2.name,
                                'other_role': prof2.role.value,
                                'my_claim': claim1.get('claim_text'),
                                'their_claim': claim2.get('claim_text'),
                                'my_doc': claim1.get('filename') or claim1.get('title'),
                                'their_doc': claim2.get('filename') or claim2.get('title')
                            }
                            prof1.contradictions_with_others.append(contradiction)
                            
                            # Add reverse
                            prof2.contradictions_with_others.append({
                                'other_professional': prof1.name,
                                'other_role': prof1.role.value,
                                'my_claim': claim2.get('claim_text'),
                                'their_claim': claim1.get('claim_text'),
                                'my_doc': claim2.get('filename') or claim2.get('title'),
                                'their_doc': claim1.get('filename') or claim1.get('title')
                            })
        
        # Recalculate scores with contradictions
        for prof in self.professionals.values():
            self._calculate_accountability_score(prof)
    
    def get_report(self) -> dict:
        """Generate a comprehensive report."""
        
        # Sort by accountability score
        sorted_professionals = sorted(
            self.professionals.values(),
            key=lambda p: p.accountability_score,
            reverse=True
        )
        
        return {
            'generated_at': datetime.now().isoformat(),
            'total_professionals': len(self.professionals),
            'by_role': self._count_by_role(),
            'top_accountability_concerns': [
                {
                    'name': p.name,
                    'role': p.role.value,
                    'organization': p.organization,
                    'score': p.accountability_score,
                    'self_contradictions': len(p.self_contradictions),
                    'contradictions_with_others': len(p.contradictions_with_others),
                    'bias_indicators': len(p.bias_indicators),
                    'complaint_routes': p.complaint_routes
                }
                for p in sorted_professionals[:20]
            ],
            'professionals': {
                p.normalized_name: {
                    'name': p.name,
                    'role': p.role.value,
                    'organization': p.organization,
                    'accountability_score': p.accountability_score,
                    'claim_count': len(p.claims),
                    'self_contradictions': p.self_contradictions[:5],
                    'contradictions_with_others': p.contradictions_with_others[:5],
                    'bias_indicators': p.bias_indicators[:10],
                    'key_quotes': p.key_quotes[:10],
                    'documents': p.documents[:10],
                    'complaint_routes': p.complaint_routes
                }
                for p in sorted_professionals
            }
        }
    
    def _count_by_role(self) -> dict:
        """Count professionals by role."""
        counts = defaultdict(int)
        for p in self.professionals.values():
            counts[p.role.value] += 1
        return dict(counts)
    
    def close(self):
        self.conn.close()


def run_professional_analysis(db_path: str, output_file: str = None):
    """Run professional accountability analysis."""
    
    tracker = ProfessionalAccountabilityTracker(db_path)
    
    try:
        tracker.analyze_all_professionals()
        report = tracker.get_report()
        
        print("\n" + "="*70)
        print("PROFESSIONAL ACCOUNTABILITY ANALYSIS")
        print("="*70)
        
        print(f"\nTotal professionals identified: {report['total_professionals']}")
        
        print("\nBy Role:")
        for role, count in report['by_role'].items():
            print(f"  {role}: {count}")
        
        print("\n" + "-"*70)
        print("TOP ACCOUNTABILITY CONCERNS")
        print("-"*70)
        
        for i, prof in enumerate(report['top_accountability_concerns'][:15], 1):
            if prof['score'] > 0:
                print(f"\n{i}. {prof['name']} ({prof['role']})")
                print(f"   Organization: {prof['organization']}")
                print(f"   Accountability Score: {prof['score']:.1f}")
                print(f"   Self-contradictions: {prof['self_contradictions']}")
                print(f"   Contradictions with others: {prof['contradictions_with_others']}")
                print(f"   Bias indicators: {prof['bias_indicators']}")
                print(f"   Complaint routes: {', '.join(prof['complaint_routes'])}")
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            print(f"\nFull report saved to: {output_file}")
        
        return report
        
    finally:
        tracker.close()


if __name__ == "__main__":
    run_professional_analysis(
        db_path="Phronesis/data/db/phronesis.db",
        output_file="data/professional_accountability_report.json"
    )

