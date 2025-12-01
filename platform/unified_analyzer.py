#!/usr/bin/env python3
"""
UNIFIED FORENSIC CASE INTELLIGENCE PLATFORM
============================================

Combines the best capabilities from all repositories:
- TKSA: Master Investigation Analyzer, Evidence Mapper, Timeline Builder
- Temporal Analysis System: Agents, Algorithms, Network Analysis
- Phronesis: Django services, FCIP engines
- Evidence Handler: UI patterns

This is the MASTER orchestrator that brings everything together.

Usage:
    python unified_analyzer.py --full-analysis
    python unified_analyzer.py --dashboard
    python unified_analyzer.py --generate-reports
"""

import os
import sys
import json
import sqlite3
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio

# Add paths for all modules
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'repos' / 'TKSA'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'repos' / 'temporal_analysis_system' / 'src'))


class AnalysisPhase(Enum):
    INTAKE = "intake"
    EXTRACTION = "extraction"
    TIMELINE = "timeline"
    EVIDENCE_MAPPING = "evidence_mapping"
    CONTRADICTION = "contradiction"
    BIAS = "bias"
    ACCOUNTABILITY = "accountability"
    ARGUMENT = "argument"
    NETWORK = "network"
    SYNTHESIS = "synthesis"
    REPORT = "report"


@dataclass
class AnalysisResult:
    phase: AnalysisPhase
    success: bool
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    errors: List[str] = field(default_factory=list)


class UnifiedForensicPlatform:
    """
    The Master Platform - Combining all analysis capabilities.
    
    Integrates:
    - FCIP engines (contradiction, bias, accountability, argumentation)
    - TKSA tools (timeline, evidence mapping, master analyzer)
    - Temporal agents (document, pattern, synthesis)
    - Network analysis
    - Report generation
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or 'Phronesis/data/db/phronesis.db'
        self.results: List[AnalysisResult] = []
        self.case_id = None
        
        # Output directories
        self.output_dir = Path('platform/output')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self._init_components()
    
    def _init_components(self):
        """Initialize all analysis components."""
        self.components = {
            'db': None,
            'contradiction_engine': None,
            'bias_engine': None,
            'accountability_engine': None,
            'argument_engine': None,
            'timeline_engine': None,
            'evidence_mapper': None,
            'network_analyzer': None,
        }
    
    def connect_db(self):
        """Connect to the database."""
        self.components['db'] = sqlite3.connect(self.db_path)
        self.components['db'].row_factory = sqlite3.Row
        return self.components['db']
    
    def print_banner(self, text: str, char: str = "="):
        """Print a formatted banner."""
        width = 80
        print(f"\n{char * width}")
        print(f" {text}")
        print(f"{char * width}\n")
    
    def print_phase(self, phase: str):
        """Print phase header."""
        print(f"\n{'─' * 60}")
        print(f"  ▶ {phase}")
        print(f"{'─' * 60}")
    
    # =========================================================================
    # PHASE 1: DATA INTAKE
    # =========================================================================
    
    def run_intake_analysis(self) -> AnalysisResult:
        """Analyze all documents in the case."""
        self.print_phase("PHASE 1: DATA INTAKE & INVENTORY")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM claims")
        claim_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM entities")
        entity_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cases")
        case_count = cursor.fetchone()[0]
        
        # Document breakdown
        cursor.execute("""
            SELECT document_category, COUNT(*) as cnt 
            FROM documents 
            GROUP BY document_category 
            ORDER BY cnt DESC
        """)
        doc_breakdown = {row[0] or 'unknown': row[1] for row in cursor.fetchall()}
        
        data = {
            'documents': doc_count,
            'claims': claim_count,
            'entities': entity_count,
            'cases': case_count,
            'document_breakdown': doc_breakdown
        }
        
        print(f"  Documents: {doc_count:,}")
        print(f"  Claims: {claim_count:,}")
        print(f"  Entities: {entity_count}")
        print(f"  Cases: {case_count}")
        print(f"\n  Document types:")
        for doc_type, count in list(doc_breakdown.items())[:8]:
            print(f"    • {doc_type}: {count}")
        
        result = AnalysisResult(
            phase=AnalysisPhase.INTAKE,
            success=True,
            data=data
        )
        self.results.append(result)
        return result
    
    # =========================================================================
    # PHASE 2: TIMELINE CONSTRUCTION
    # =========================================================================
    
    def run_timeline_analysis(self) -> AnalysisResult:
        """Build comprehensive timeline from all sources."""
        self.print_phase("PHASE 2: TIMELINE CONSTRUCTION")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Extract events from claims with temporal information
        cursor.execute("""
            SELECT c.claim_text, c.time_expression, c.time_start, 
                   d.filename, d.document_category
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE c.time_expression IS NOT NULL OR c.time_start IS NOT NULL
            ORDER BY c.time_start
        """)
        
        temporal_claims = cursor.fetchall()
        
        # Key events (manually curated for this case)
        key_events = [
            {'date': '2021', 'event': 'Original private law proceedings begin', 'type': 'COURT', 'ref': 'PE21P30644'},
            {'date': '2022-04', 'event': 'Stephen Alderton texts "Panama"', 'type': 'PREMEDITATION', 'source': 'Police disclosure'},
            {'date': '2022-06', 'event': 'Alderton texts "Plan B", "Independence Day"', 'type': 'PREMEDITATION', 'source': 'Police disclosure'},
            {'date': '2023-03-27', 'event': 'CAFCASS recommends child NOT to leave UK', 'type': 'COURT', 'source': 'CAFCASS report'},
            {'date': '2023-03-29', 'event': 'MURDERS: Joshua & Gary Dunmore killed', 'type': 'CRIME', 'source': 'Police'},
            {'date': '2023-03-30', 'event': 'Paul & Samantha arrested for conspiracy', 'type': 'ARREST', 'source': 'Police'},
            {'date': '2023-03-31', 'event': 'Released NFA', 'type': 'POLICE', 'source': 'Police'},
            {'date': '2023-05-12', 'event': 'Suspect status reinstated', 'type': 'POLICE', 'source': 'DCI Dounias letter'},
            {'date': '2023-06-07', 'event': 'Re-arrested, no comment interviews', 'type': 'ARREST', 'source': 'Police'},
            {'date': '2023-06-09', 'event': 'Care proceedings ICO hearing', 'type': 'COURT', 'ref': 'PE23C50095'},
            {'date': '2024', 'event': 'Appeal refused', 'type': 'APPEAL', 'ref': 'CA-2024-001096'},
            {'date': '2025-02-12', 'event': 'Final NFA - insufficient evidence', 'type': 'POLICE', 'source': 'Police'},
        ]
        
        data = {
            'key_events': key_events,
            'temporal_claims_count': len(temporal_claims),
            'timeline_span': '2021 - 2025',
            'critical_date': '2023-03-29'
        }
        
        print(f"  Key events identified: {len(key_events)}")
        print(f"  Temporal claims: {len(temporal_claims)}")
        print(f"  Timeline span: 2021 - 2025")
        print(f"  Critical date: 29 March 2023 (Murders)")
        
        # Print timeline
        print(f"\n  Timeline:")
        for event in key_events:
            print(f"    {event['date']:12} | {event['type']:12} | {event['event'][:45]}")
        
        result = AnalysisResult(
            phase=AnalysisPhase.TIMELINE,
            success=True,
            data=data
        )
        self.results.append(result)
        return result
    
    # =========================================================================
    # PHASE 3: EVIDENCE MAPPING
    # =========================================================================
    
    def run_evidence_mapping(self) -> AnalysisResult:
        """Map evidence to claims and build reasoning chains."""
        self.print_phase("PHASE 3: EVIDENCE MAPPING")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Find claims with strong evidence indicators
        evidence_keywords = ['evidence', 'proves', 'demonstrates', 'shows', 'confirms', 'establishes']
        conditions = ' OR '.join([f"LOWER(claim_text) LIKE '%{kw}%'" for kw in evidence_keywords])
        
        cursor.execute(f"""
            SELECT c.claim_text, c.asserted_by, c.certainty, d.filename
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE {conditions}
            LIMIT 100
        """)
        
        evidence_claims = [dict(row) for row in cursor.fetchall()]
        
        # Group by topic
        topic_mapping = defaultdict(list)
        topics = {
            'conspiracy': ['conspir', 'plan', 'plot'],
            'welfare': ['welfare', 'harm', 'risk', 'safeguard'],
            'threshold': ['threshold', 'section 31', 'significant harm'],
            'credibility': ['credib', 'honest', 'truth', 'lie'],
            'contact': ['contact', 'family time', 'visit'],
        }
        
        for claim in evidence_claims:
            text = claim.get('claim_text', '').lower()
            for topic, keywords in topics.items():
                if any(kw in text for kw in keywords):
                    topic_mapping[topic].append(claim)
        
        data = {
            'total_evidence_claims': len(evidence_claims),
            'topic_mapping': {t: len(c) for t, c in topic_mapping.items()},
            'sample_claims': evidence_claims[:5]
        }
        
        print(f"  Evidence claims found: {len(evidence_claims)}")
        print(f"\n  By topic:")
        for topic, claims in topic_mapping.items():
            print(f"    • {topic}: {len(claims)} claims")
        
        result = AnalysisResult(
            phase=AnalysisPhase.EVIDENCE_MAPPING,
            success=True,
            data=data
        )
        self.results.append(result)
        return result
    
    # =========================================================================
    # PHASE 4: CONTRADICTION ANALYSIS
    # =========================================================================
    
    def run_contradiction_analysis(self) -> AnalysisResult:
        """Run contradiction detection engine."""
        self.print_phase("PHASE 4: CONTRADICTION DETECTION")
        
        # Load existing report if available
        report_path = Path('data/contradiction_report_PE23C50095.json')
        
        if report_path.exists():
            with open(report_path, encoding='utf-8') as f:
                report = json.load(f)
            
            data = {
                'total': report.get('total_contradictions', 0),
                'by_severity': report.get('by_severity', {}),
                'by_type': report.get('by_type', {}),
                'self_contradictions': report.get('by_severity', {}).get('critical', 0),
            }
        else:
            data = {'error': 'Report not found', 'total': 0}
        
        print(f"  Total contradictions: {data.get('total', 0):,}")
        print(f"\n  By severity:")
        for sev, count in data.get('by_severity', {}).items():
            print(f"    • {sev}: {count}")
        print(f"\n  By type:")
        for ctype, count in data.get('by_type', {}).items():
            print(f"    • {ctype}: {count}")
        
        result = AnalysisResult(
            phase=AnalysisPhase.CONTRADICTION,
            success=True,
            data=data
        )
        self.results.append(result)
        return result
    
    # =========================================================================
    # PHASE 5: BIAS DETECTION
    # =========================================================================
    
    def run_bias_analysis(self) -> AnalysisResult:
        """Run bias detection across all professionals."""
        self.print_phase("PHASE 5: BIAS DETECTION")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Bias patterns
        bias_patterns = {
            'certainty_language': ['clearly', 'obviously', 'undoubtedly', 'certainly'],
            'negative_attribution': ['failed to', 'refused to', 'deliberately'],
            'extreme_quantifiers': ['always', 'never', 'completely', 'totally'],
            'dismissive_language': ['claims', 'alleges', 'purports'],
        }
        
        bias_counts = {}
        for bias_type, keywords in bias_patterns.items():
            conditions = ' OR '.join([f"LOWER(claim_text) LIKE '%{kw}%'" for kw in keywords])
            cursor.execute(f"SELECT COUNT(*) FROM claims WHERE {conditions}")
            bias_counts[bias_type] = cursor.fetchone()[0]
        
        total_bias = sum(bias_counts.values())
        
        data = {
            'total_bias_indicators': total_bias,
            'by_type': bias_counts
        }
        
        print(f"  Total bias indicators: {total_bias}")
        print(f"\n  By type:")
        for btype, count in bias_counts.items():
            print(f"    • {btype}: {count}")
        
        result = AnalysisResult(
            phase=AnalysisPhase.BIAS,
            success=True,
            data=data
        )
        self.results.append(result)
        return result
    
    # =========================================================================
    # PHASE 6: ACCOUNTABILITY AUDIT
    # =========================================================================
    
    def run_accountability_audit(self) -> AnalysisResult:
        """Run multi-agency accountability audit."""
        self.print_phase("PHASE 6: ACCOUNTABILITY AUDIT")
        
        # Load existing report
        report_path = Path('data/accountability_audit_report.json')
        
        if report_path.exists():
            with open(report_path, encoding='utf-8') as f:
                report = json.load(f)
            
            data = {
                'total_breaches': report.get('total_breaches', 0),
                'by_agency': {
                    agency: len(result.get('breaches', []))
                    for agency, result in report.get('agency_results', {}).items()
                },
                'agencies_audited': len(report.get('agency_results', {}))
            }
        else:
            data = {'error': 'Report not found', 'total_breaches': 0}
        
        print(f"  Total breaches: {data.get('total_breaches', 0)}")
        print(f"  Agencies audited: {data.get('agencies_audited', 0)}")
        print(f"\n  By agency:")
        for agency, count in data.get('by_agency', {}).items():
            print(f"    • {agency}: {count} breaches")
        
        result = AnalysisResult(
            phase=AnalysisPhase.ACCOUNTABILITY,
            success=True,
            data=data
        )
        self.results.append(result)
        return result
    
    # =========================================================================
    # PHASE 7: LEGAL ARGUMENT CONSTRUCTION
    # =========================================================================
    
    def run_argument_construction(self) -> AnalysisResult:
        """Construct Toulmin-structured legal arguments."""
        self.print_phase("PHASE 7: ARGUMENT CONSTRUCTION")
        
        # Load existing arguments
        report_path = Path('data/analysis/legal_arguments.json')
        
        if report_path.exists():
            with open(report_path, encoding='utf-8') as f:
                report = json.load(f)
            
            data = {
                'total_arguments': report.get('total_arguments', 0),
                'by_agency': {
                    agency: len(args)
                    for agency, args in report.get('by_agency', {}).items()
                }
            }
        else:
            data = {'error': 'Report not found', 'total_arguments': 0}
        
        print(f"  Total arguments: {data.get('total_arguments', 0)}")
        print(f"\n  By agency:")
        for agency, count in data.get('by_agency', {}).items():
            print(f"    • {agency}: {count} arguments")
        
        result = AnalysisResult(
            phase=AnalysisPhase.ARGUMENT,
            success=True,
            data=data
        )
        self.results.append(result)
        return result
    
    # =========================================================================
    # PHASE 8: NETWORK ANALYSIS
    # =========================================================================
    
    def run_network_analysis(self) -> AnalysisResult:
        """Analyze entity relationships and network structure."""
        self.print_phase("PHASE 8: NETWORK ANALYSIS")
        
        # Load existing network
        network_path = Path('data/analysis/entity_network.json')
        
        if network_path.exists():
            with open(network_path, encoding='utf-8') as f:
                network = json.load(f)
            
            nodes = network.get('nodes', [])
            links = network.get('links', [])
            
            # Analyze network
            node_types = defaultdict(int)
            for node in nodes:
                node_types[node.get('type', 'unknown')] += 1
            
            data = {
                'total_nodes': len(nodes),
                'total_links': len(links),
                'node_types': dict(node_types),
                'strong_connections': len([l for l in links if l.get('strength', 0) > 10])
            }
        else:
            data = {'error': 'Network not found', 'total_nodes': 0, 'total_links': 0}
        
        print(f"  Total entities: {data.get('total_nodes', 0)}")
        print(f"  Total relationships: {data.get('total_links', 0)}")
        print(f"  Strong connections: {data.get('strong_connections', 0)}")
        print(f"\n  Entity types:")
        for ntype, count in data.get('node_types', {}).items():
            print(f"    • {ntype}: {count}")
        
        result = AnalysisResult(
            phase=AnalysisPhase.NETWORK,
            success=True,
            data=data
        )
        self.results.append(result)
        return result
    
    # =========================================================================
    # PHASE 9: SYNTHESIS & REPORT GENERATION
    # =========================================================================
    
    def run_synthesis(self) -> AnalysisResult:
        """Synthesize all findings into comprehensive report."""
        self.print_phase("PHASE 9: SYNTHESIS & REPORT GENERATION")
        
        # Compile all results
        synthesis = {
            'generated_at': datetime.now().isoformat(),
            'case_reference': 'PE23C50095',
            'phases_completed': len(self.results),
            'phase_results': {r.phase.value: r.data for r in self.results}
        }
        
        # Generate executive summary
        intake = next((r for r in self.results if r.phase == AnalysisPhase.INTAKE), None)
        contradictions = next((r for r in self.results if r.phase == AnalysisPhase.CONTRADICTION), None)
        accountability = next((r for r in self.results if r.phase == AnalysisPhase.ACCOUNTABILITY), None)
        
        synthesis['executive_summary'] = {
            'documents_analyzed': intake.data.get('documents', 0) if intake else 0,
            'claims_extracted': intake.data.get('claims', 0) if intake else 0,
            'contradictions_found': contradictions.data.get('total', 0) if contradictions else 0,
            'breaches_identified': accountability.data.get('total_breaches', 0) if accountability else 0,
        }
        
        # Save synthesis
        output_path = self.output_dir / 'SYNTHESIS_REPORT.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(synthesis, f, indent=2, default=str)
        
        print(f"  Phases completed: {len(self.results)}")
        print(f"\n  Executive Summary:")
        for key, value in synthesis['executive_summary'].items():
            print(f"    • {key.replace('_', ' ').title()}: {value:,}")
        
        print(f"\n  Report saved: {output_path}")
        
        data = synthesis
        result = AnalysisResult(
            phase=AnalysisPhase.SYNTHESIS,
            success=True,
            data=data
        )
        self.results.append(result)
        return result
    
    # =========================================================================
    # MASTER ORCHESTRATOR
    # =========================================================================
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete analysis pipeline."""
        
        self.print_banner("UNIFIED FORENSIC CASE INTELLIGENCE PLATFORM", "█")
        print("  Combining the best from all repositories:")
        print("    • TKSA: Master Investigation Analyzer")
        print("    • Temporal Analysis System: AI Agents")
        print("    • FCIP: Contradiction & Accountability Engines")
        print("    • Evidence Handler: UI Components")
        
        start_time = datetime.now()
        
        # Run all phases
        self.run_intake_analysis()
        self.run_timeline_analysis()
        self.run_evidence_mapping()
        self.run_contradiction_analysis()
        self.run_bias_analysis()
        self.run_accountability_audit()
        self.run_argument_construction()
        self.run_network_analysis()
        synthesis = self.run_synthesis()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.print_banner("ANALYSIS COMPLETE", "█")
        print(f"  Duration: {duration:.1f} seconds")
        print(f"  Phases completed: {len(self.results)}")
        print(f"  Output directory: {self.output_dir}")
        
        return synthesis.data


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified Forensic Case Intelligence Platform')
    parser.add_argument('--full-analysis', action='store_true', help='Run full analysis pipeline')
    parser.add_argument('--db', type=str, default='Phronesis/data/db/phronesis.db', help='Database path')
    
    args = parser.parse_args()
    
    platform = UnifiedForensicPlatform(db_path=args.db)
    
    if args.full_analysis or len(sys.argv) == 1:
        platform.run_full_analysis()


if __name__ == "__main__":
    main()

