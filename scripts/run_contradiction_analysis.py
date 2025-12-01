"""
Run Contradiction Analysis on PE23C50095
Analyzes 3,521 claims across 565 documents spanning 2021-2025
"""
import sqlite3
import sys
import os
from datetime import datetime
from uuid import uuid4, UUID

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the contradiction engine
from fcip.engines.contradiction import ContradictionDetectionEngine, ContradictionType
from fcip.models.core import Claim, ClaimType, Modality, Polarity, Confidence

def load_claims_from_phronesis_db():
    """Load claims from the Phronesis database."""
    db_path = 'Phronesis/data/db/phronesis.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all claims with document info
    cursor.execute("""
        SELECT c.*, d.filename, d.document_category, d.title as doc_title
        FROM claims c
        LEFT JOIN documents d ON c.document_id = d.id
        WHERE c.case_id = '815e9a07b595417784ef15dd4d3e6b4c'
        ORDER BY c.created_at
    """)
    
    rows = cursor.fetchall()
    print(f"Loaded {len(rows)} claims from database")
    
    claims = []
    errors = 0
    for row in rows:
        try:
            # Parse modality
            modality_str = (row['modality'] or 'asserted').lower()
            modality = Modality.ASSERTED
            for m in Modality:
                if m.value == modality_str:
                    modality = m
                    break
            
            # Parse polarity  
            polarity_str = (row['polarity'] or 'affirm').lower()
            polarity = Polarity.AFFIRM if polarity_str == 'affirm' else Polarity.NEGATE
            
            # Parse claim type
            claim_type_str = (row['claim_type'] or 'assertion').lower()
            claim_type = ClaimType.ASSERTION
            for ct in ClaimType:
                if ct.value == claim_type_str:
                    claim_type = ct
                    break
            
            # Get certainty value
            certainty_val = row['certainty'] if row['certainty'] is not None else (row['ai_confidence'] or 0.5)
            certainty_val = float(certainty_val)
            
            # Create UUID from hex string
            claim_id_str = row['id']
            doc_id_str = row['document_id'] or ''
            
            claim = Claim(
                claim_id=UUID(claim_id_str) if len(claim_id_str) == 32 else uuid4(),
                document_id=UUID(doc_id_str) if doc_id_str and len(doc_id_str) == 32 else uuid4(),
                case_id=row['case_id'],
                text=row['claim_text'] or '',
                claim_type=claim_type,
                source_quote=row['context'],
                subject=row['target_entity'],
                predicate=row['claim_type'],
                predicate_category=row['claim_type'],
                modality=modality,
                polarity=polarity,
                certainty=certainty_val,
                asserted_by=row['asserted_by'] or row['claimant_capacity'],
                time_expression=row['time_expression'] if 'time_expression' in row.keys() else None,
                confidence=Confidence.llm_extracted(certainty_val, 'claude')
            )
            claims.append(claim)
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  Error converting claim: {e}")
            continue
    
    if errors > 0:
        print(f"  ({errors} claims had conversion errors)")
    
    conn.close()
    return claims

def main():
    print("=" * 60)
    print("CONTRADICTION ANALYSIS - PE23C50095")
    print("JFD vs SJS Family Proceedings (2021-2025)")
    print("=" * 60)
    print()
    
    # Load claims
    print("Loading claims from Phronesis database...")
    claims = load_claims_from_phronesis_db()
    print(f"Successfully loaded {len(claims)} claims for analysis")
    print()
    
    if len(claims) < 2:
        print("Not enough claims to analyze")
        return
    
    # Initialize engine
    print("Initializing Contradiction Detection Engine...")
    engine = ContradictionDetectionEngine(
        semantic_threshold=0.55,  # Lower threshold for more matches
        polarity_threshold=0.7,
        enable_semantic=True  # Use semantic similarity if available
    )
    
    # Run detection
    print("Running contradiction detection...")
    print("(This may take a few minutes with 3,500+ claims)")
    print()
    
    start = datetime.now()
    report = engine.detect_contradictions(claims, 'PE23C50095')
    duration = (datetime.now() - start).total_seconds()
    
    print(f"Analysis completed in {duration:.1f} seconds")
    print()
    
    # Extract contradictions list from report
    contradictions = report.contradictions if hasattr(report, 'contradictions') else []
    
    print("=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total contradictions found: {report.total_contradictions}")
    print()
    print("By Severity:")
    for sev, count in report.by_severity.items():
        if count > 0:
            print(f"  {sev.upper()}: {count}")
    print()
    print("By Type:")
    for ctype, count in report.by_type.items():
        if count > 0:
            label = {
                'direct': 'Direct Contradictions',
                'temporal': 'Temporal Conflicts',
                'self_contradiction': 'Self-Contradictions',
                'modality_shift': 'Allegation → Fact',
                'value': 'Value Conflicts',
                'attribution': 'Attribution Disputes'
            }.get(ctype, ctype)
            print(f"  {label}: {count}")
    
    # Show top contradictions
    print()
    print("=" * 60)
    print("TOP 10 MOST SIGNIFICANT FINDINGS")
    print("=" * 60)
    
    for i, c in enumerate(report.contradictions[:10], 1):
        print()
        severity = c.severity.value if hasattr(c.severity, 'value') else str(c.severity)
        ctype = c.contradiction_type.value if hasattr(c.contradiction_type, 'value') else str(c.contradiction_type)
        print(f"#{i} [{severity.upper()}] {ctype}")
        print(f"   Author A: {c.claim_a_author or c.claim_a_source or 'Unknown'}")
        print(f"   Author B: {c.claim_b_author or c.claim_b_source or 'Unknown'}")
        if c.same_author:
            print(f"   *** SAME AUTHOR - SELF CONTRADICTION ***")
        if c.claim_a_text:
            text_a = c.claim_a_text[:100] + "..." if len(c.claim_a_text) > 100 else c.claim_a_text
            print(f"   Claim A: \"{text_a}\"")
        if c.claim_b_text:
            text_b = c.claim_b_text[:100] + "..." if len(c.claim_b_text) > 100 else c.claim_b_text
            print(f"   Claim B: \"{text_b}\"")
    
    # Save full report
    import json
    report_path = 'data/contradiction_report_PE23C50095.json'
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    # Convert report to dict for JSON
    def get_enum_value(x):
        return x.value if hasattr(x, 'value') else str(x)
    
    report_dict = {
        'case_id': report.case_id,
        'total_contradictions': report.total_contradictions,
        'by_severity': report.by_severity,
        'by_type': report.by_type,
        'contradictions': [
            {
                'id': str(c.contradiction_id),
                'type': get_enum_value(c.contradiction_type),
                'severity': get_enum_value(c.severity),
                'same_author': c.same_author,
                'author_a': c.claim_a_author,
                'author_b': c.claim_b_author,
                'source_a': c.claim_a_source,
                'source_b': c.claim_b_source,
                'text_a': c.claim_a_text,
                'text_b': c.claim_b_text,
                'semantic_similarity': c.semantic_similarity,
            }
            for c in report.contradictions
        ]
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_dict, f, indent=2, default=str, ensure_ascii=False)
    print()
    print(f"Full report saved to: {report_path}")
    
    # Highlight critical findings - self-contradictions
    self_contradictions = [c for c in report.contradictions 
                          if c.contradiction_type == ContradictionType.SELF_CONTRADICTION or c.same_author]
    
    if self_contradictions:
        print()
        print("=" * 60)
        print(f"CRITICAL: {len(self_contradictions)} SELF-CONTRADICTIONS")
        print("=" * 60)
        print("Professionals/witnesses contradicting their own statements")
        print("Highly significant for credibility (Lucas direction applies)")
        
        # Group by author
        by_author = {}
        for sc in self_contradictions:
            author = sc.claim_a_author or sc.claim_a_source or 'Unknown'
            if author not in by_author:
                by_author[author] = []
            by_author[author].append(sc)
        
        print(f"\nSelf-contradictions by author:")
        for author, contradictions in sorted(by_author.items(), key=lambda x: -len(x[1]))[:10]:
            print(f"\n  {author}: {len(contradictions)} self-contradiction(s)")
            for j, sc in enumerate(contradictions[:2], 1):
                text_a = sc.claim_a_text[:60] + "..." if sc.claim_a_text and len(sc.claim_a_text) > 60 else (sc.claim_a_text or "")
                text_b = sc.claim_b_text[:60] + "..." if sc.claim_b_text and len(sc.claim_b_text) > 60 else (sc.claim_b_text or "")
                print(f"    {j}. \"{text_a}\"")
                print(f"       vs \"{text_b}\"")

if __name__ == '__main__':
    main()

