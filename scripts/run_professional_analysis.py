"""Run professional accountability analysis - standalone version."""
import sqlite3
import json
import re
import os
from datetime import datetime
from collections import defaultdict
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


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


# Known professionals mapping
KNOWN_PROFESSIONALS = {
    'dci katie dounias': (ProfessionalRole.POLICE_OFFICER, 'Beds, Cambs & Herts Major Crime Unit'),
    'dc 2072 atkinson': (ProfessionalRole.POLICE_OFFICER, 'Cambridgeshire Constabulary'),
    'dc atkinson': (ProfessionalRole.POLICE_OFFICER, 'Cambridgeshire Constabulary'),
    'paul duggan': (ProfessionalRole.SOCIAL_WORKER, 'Cambridgeshire County Council'),
    'lucy ardern': (ProfessionalRole.SOCIAL_WORKER, 'Cambridgeshire County Council'),
    'sreenadh puthanpurakkal': (ProfessionalRole.SOCIAL_WORKER, 'Cambridgeshire County Council'),
    'butler': (ProfessionalRole.SOCIAL_WORKER, 'Cambridgeshire County Council'),
    'guardian': (ProfessionalRole.CAFCASS_OFFICER, 'CAFCASS'),
    'hhj gordon-saker': (ProfessionalRole.JUDGE, 'Family Court Peterborough'),
    'gordon-saker': (ProfessionalRole.JUDGE, 'Family Court Peterborough'),
    'the court': (ProfessionalRole.JUDGE, 'Family Court'),
    'dr vivien wong-spracklen': (ProfessionalRole.EXPERT, 'Psychology'),
    'samantha stephen': (ProfessionalRole.PARTY, 'Mother/Respondent'),
    'paul stephen': (ProfessionalRole.PARTY, 'Father/Respondent'),
    'mandy seamark': (ProfessionalRole.PARTY, 'Paternal Grandmother'),
    'local authority': (ProfessionalRole.LOCAL_AUTHORITY, 'Cambridgeshire County Council'),
    'mother': (ProfessionalRole.PARTY, 'Mother/Respondent'),
    'father': (ProfessionalRole.PARTY, 'Father/Respondent'),
}

BIAS_PATTERNS = {
    'certainty_language': [r'\bclearly\b', r'\bobviously\b', r'\bundoubtedly\b', r'\bcertainly\b'],
    'negative_attribution': [r'\bfailed to\b', r'\brefused to\b', r'\bdeliberately\b'],
    'extreme_quantifiers': [r'\balways\b', r'\bnever\b', r'\bcompletely\b', r'\btotally\b'],
    'emotional_language': [r'\bshocking\b', r'\bappalling\b', r'\bdisturbing\b', r'\balarming\b'],
    'dismissive_language': [r'\bclaims\b', r'\balleges\b', r'\bpurports\b'],
}

COMPLAINT_ROUTES = {
    ProfessionalRole.POLICE_OFFICER: ['IOPC', 'Police Professional Standards'],
    ProfessionalRole.SOCIAL_WORKER: ['HCPC Fitness to Practise', 'Employer', 'LGSCO'],
    ProfessionalRole.CAFCASS_OFFICER: ['CAFCASS Complaints', 'Parliamentary Ombudsman'],
    ProfessionalRole.JUDGE: ['JCIO (Judicial Conduct)', 'Appeal'],
    ProfessionalRole.LOCAL_AUTHORITY: ['LGSCO', 'Internal Complaints', 'Judicial Review'],
    ProfessionalRole.EXPERT: ['Professional Body', 'Court'],
}


def normalize_name(name: str) -> str:
    if not name:
        return "unknown"
    name = name.lower().strip()
    name = re.sub(r'\s*\(.*?\)\s*', '', name)
    return name.strip()


def identify_role(normalized_name: str) -> Tuple[ProfessionalRole, Optional[str]]:
    for known_name, (role, org) in KNOWN_PROFESSIONALS.items():
        if known_name in normalized_name or normalized_name in known_name:
            return role, org
    
    if 'social worker' in normalized_name or ' sw' in normalized_name:
        return ProfessionalRole.SOCIAL_WORKER, 'Unknown'
    if 'guardian' in normalized_name or 'cafcass' in normalized_name:
        return ProfessionalRole.CAFCASS_OFFICER, 'CAFCASS'
    if 'judge' in normalized_name or 'hhj' in normalized_name:
        return ProfessionalRole.JUDGE, 'Family Court'
    if 'dc ' in normalized_name or 'police' in normalized_name:
        return ProfessionalRole.POLICE_OFFICER, 'Police'
    if 'mother' in normalized_name or 'father' in normalized_name:
        return ProfessionalRole.PARTY, 'Party'
    if 'local authority' in normalized_name:
        return ProfessionalRole.LOCAL_AUTHORITY, 'Local Authority'
    
    return ProfessionalRole.UNKNOWN, None


def analyze_bias(claims: List[dict]) -> List[dict]:
    bias_indicators = []
    for claim in claims:
        text = (claim.get('claim_text') or '').lower()
        for bias_type, patterns in BIAS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    bias_indicators.append({
                        'type': bias_type,
                        'claim_text': claim.get('claim_text'),
                        'document': claim.get('filename') or claim.get('title')
                    })
                    break
    return bias_indicators


def find_self_contradictions(claims: List[dict]) -> List[dict]:
    contradictions = []
    polarity_pairs = [('did', 'did not'), ('was', 'was not'), ('has', 'has not'), 
                      ('is', 'is not'), ('agreed', 'refused')]
    
    for i, claim1 in enumerate(claims):
        text1 = (claim1.get('claim_text') or '').lower()
        for claim2 in claims[i+1:]:
            text2 = (claim2.get('claim_text') or '').lower()
            
            for pos, neg in polarity_pairs:
                if (pos in text1 and neg in text2) or (neg in text1 and pos in text2):
                    common = set(text1.split()) & set(text2.split())
                    if len(common) > 5:
                        contradictions.append({
                            'claim_1': claim1.get('claim_text'),
                            'claim_2': claim2.get('claim_text'),
                            'doc_1': claim1.get('filename') or claim1.get('title'),
                            'doc_2': claim2.get('filename') or claim2.get('title')
                        })
                        break
    return contradictions


def run_analysis():
    print("="*70)
    print("PROFESSIONAL ACCOUNTABILITY ANALYSIS")
    print("="*70)
    
    conn = sqlite3.connect('Phronesis/data/db/phronesis.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Load claims
    cursor.execute("""
        SELECT c.*, d.filename, d.title, d.document_category
        FROM claims c
        LEFT JOIN documents d ON c.document_id = d.id
        WHERE c.asserted_by IS NOT NULL
    """)
    claims = [dict(row) for row in cursor.fetchall()]
    print(f"\nLoaded {len(claims)} claims with authors")
    
    # Group by author
    claims_by_author = defaultdict(list)
    for claim in claims:
        author = normalize_name(claim.get('asserted_by', ''))
        if author and author != 'unknown':
            claims_by_author[author].append(claim)
    
    print(f"Found {len(claims_by_author)} unique authors")
    
    # Analyze each author
    professionals = []
    
    for author, author_claims in claims_by_author.items():
        role, org = identify_role(author)
        bias = analyze_bias(author_claims)
        contradictions = find_self_contradictions(author_claims)
        
        score = len(contradictions) * 10 + len(bias) * 2
        if role in [ProfessionalRole.SOCIAL_WORKER, ProfessionalRole.CAFCASS_OFFICER, 
                    ProfessionalRole.POLICE_OFFICER, ProfessionalRole.JUDGE]:
            score *= 1.5
        
        routes = COMPLAINT_ROUTES.get(role, ['Seek legal advice'])
        
        professionals.append({
            'name': author_claims[0].get('asserted_by', author),
            'normalized': author,
            'role': role.value,
            'organization': org,
            'claim_count': len(author_claims),
            'self_contradictions': len(contradictions),
            'bias_indicators': len(bias),
            'accountability_score': score,
            'complaint_routes': routes,
            'contradiction_examples': contradictions[:3],
            'bias_examples': bias[:5],
            'documents': list(set(c.get('filename') or c.get('title') or '' for c in author_claims))[:10]
        })
    
    # Sort by accountability score
    professionals.sort(key=lambda x: x['accountability_score'], reverse=True)
    
    # Print results
    print("\n" + "-"*70)
    print("TOP ACCOUNTABILITY CONCERNS")
    print("-"*70)
    
    for i, prof in enumerate(professionals[:20], 1):
        if prof['accountability_score'] > 0:
            print(f"\n{i}. {prof['name']}")
            print(f"   Role: {prof['role']} | Org: {prof['organization']}")
            print(f"   Claims: {prof['claim_count']} | Score: {prof['accountability_score']:.1f}")
            print(f"   Self-contradictions: {prof['self_contradictions']}")
            print(f"   Bias indicators: {prof['bias_indicators']}")
            print(f"   Complaint routes: {', '.join(prof['complaint_routes'])}")
            
            if prof['contradiction_examples']:
                print(f"   Example contradiction:")
                ex = prof['contradiction_examples'][0]
                print(f"     \"{ex['claim_1'][:60]}...\"")
                print(f"     vs \"{ex['claim_2'][:60]}...\"")
    
    # Summary by role
    print("\n" + "-"*70)
    print("SUMMARY BY ROLE")
    print("-"*70)
    
    role_summary = defaultdict(lambda: {'count': 0, 'total_score': 0, 'contradictions': 0, 'bias': 0})
    for prof in professionals:
        role = prof['role']
        role_summary[role]['count'] += 1
        role_summary[role]['total_score'] += prof['accountability_score']
        role_summary[role]['contradictions'] += prof['self_contradictions']
        role_summary[role]['bias'] += prof['bias_indicators']
    
    for role, data in sorted(role_summary.items(), key=lambda x: x[1]['total_score'], reverse=True):
        print(f"\n{role.upper()}:")
        print(f"  Individuals: {data['count']}")
        print(f"  Total score: {data['total_score']:.1f}")
        print(f"  Total contradictions: {data['contradictions']}")
        print(f"  Total bias indicators: {data['bias']}")
    
    # Save report
    os.makedirs('data', exist_ok=True)
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_professionals': len(professionals),
        'professionals': professionals,
        'role_summary': dict(role_summary)
    }
    
    with open('data/professional_accountability_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n\nFull report saved to: data/professional_accountability_report.json")
    
    conn.close()


if __name__ == "__main__":
    run_analysis()

