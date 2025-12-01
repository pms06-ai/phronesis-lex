"""
Accountability Audit Engine

Systematically analyzes case documents against statutory duties to identify
breaches, procedural failures, and grounds for complaint/appeal.

This is the core engine for legitimate accountability - documenting exactly
where each agency failed to meet its legal obligations.
"""

import re
import sqlite3
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from enum import Enum
from collections import defaultdict
import json

# Import statutory duties
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.statutory_duties import (
    Agency, BreachSeverity, StatutoryDuty,
    ALL_STATUTORY_DUTIES, DUTIES_BY_AGENCY, get_complaint_routes
)


@dataclass
class BreachEvidence:
    """Evidence of a potential breach."""
    document_id: str
    document_name: str
    claim_id: Optional[str]
    claim_text: str
    date: Optional[str]
    author: Optional[str]
    page_reference: Optional[str]
    context: str


@dataclass 
class IdentifiedBreach:
    """A specific identified breach of statutory duty."""
    duty: StatutoryDuty
    breach_indicator_matched: str
    evidence: List[BreachEvidence]
    analysis: str
    severity: BreachSeverity
    complaint_ready: bool = False
    

@dataclass
class AgencyReport:
    """Accountability report for a single agency."""
    agency: Agency
    total_breaches: int
    critical_breaches: int
    serious_breaches: int
    breaches: List[IdentifiedBreach]
    complaint_routes: List[str]
    summary: str


@dataclass
class AccountabilityReport:
    """Full accountability report across all agencies."""
    case_reference: str
    generated_at: str
    agencies_analyzed: List[Agency]
    agency_reports: Dict[Agency, AgencyReport]
    total_breaches: int
    critical_findings: List[str]
    recommended_actions: List[str]
    
    def to_dict(self) -> dict:
        return {
            'case_reference': self.case_reference,
            'generated_at': self.generated_at,
            'agencies_analyzed': [a.value for a in self.agencies_analyzed],
            'total_breaches': self.total_breaches,
            'critical_findings': self.critical_findings,
            'recommended_actions': self.recommended_actions,
            'agency_reports': {
                agency.value: {
                    'total_breaches': report.total_breaches,
                    'critical_breaches': report.critical_breaches,
                    'serious_breaches': report.serious_breaches,
                    'summary': report.summary,
                    'complaint_routes': report.complaint_routes,
                    'breaches': [
                        {
                            'duty_id': b.duty.id,
                            'duty_title': b.duty.title,
                            'legal_basis': b.duty.legal_basis,
                            'breach_indicator': b.breach_indicator_matched,
                            'severity': b.severity.value,
                            'analysis': b.analysis,
                            'evidence_count': len(b.evidence),
                            'evidence': [
                                {
                                    'document': e.document_name,
                                    'claim': e.claim_text[:200] + '...' if len(e.claim_text) > 200 else e.claim_text,
                                    'date': e.date,
                                    'author': e.author
                                }
                                for e in b.evidence[:5]  # Limit to first 5
                            ]
                        }
                        for b in report.breaches
                    ]
                }
                for agency, report in self.agency_reports.items()
            }
        }


class AccountabilityAuditEngine:
    """
    Engine for auditing case documents against statutory duties.
    
    This systematically checks for evidence of breaches by each agency
    and generates actionable reports for complaints and legal proceedings.
    """
    
    # Keyword patterns for identifying agency-related content
    AGENCY_KEYWORDS = {
        Agency.POLICE: [
            r'\bpolice\b', r'\bconstabulary\b', r'\bdetective\b', r'\bdc\b', r'\bdci\b',
            r'\barrest\b', r'\bbail\b', r'\binvestigation\b', r'\boperation scan\b',
            r'\bmurder\b', r'\bconspiracy\b', r'\bpace\b', r'\bcaution\b'
        ],
        Agency.LOCAL_AUTHORITY: [
            r'\blocal authority\b', r'\bcouncil\b', r'\bcambridgeshire\b', r'\bla\b',
            r'\bcare proceedings\b', r'\bsection 31\b', r'\bsection 47\b', r'\bico\b',
            r'\binterim care\b', r'\bcare plan\b', r'\bthreshold\b'
        ],
        Agency.CAFCASS: [
            r'\bcafcass\b', r'\bguardian\b', r'\bsection 7\b', r'\brule 16\b',
            r'\bchildren.s guardian\b', r'\bfamily court adviser\b'
        ],
        Agency.SOCIAL_WORKER: [
            r'\bsocial worker\b', r'\bsw\b', r'\bassessment\b', r'\bvisit\b',
            r'\bchild protection\b', r'\bsafeguarding\b', r'\bcase conference\b'
        ],
        Agency.FAMILY_COURT: [
            r'\bjudge\b', r'\bhearing\b', r'\bcourt\b', r'\border\b', r'\bjudgment\b',
            r'\bhhj\b', r'\brecorder\b', r'\bdjm\b', r'\bdistrict judge\b'
        ],
        Agency.MEDIA: [
            r'\bchannel 4\b', r'\b24 hours\b', r'\bcustody\b', r'\bfilming\b',
            r'\bdocumentary\b', r'\bmedia\b', r'\bbroadcast\b', r'\bpress\b'
        ],
        Agency.APPEAL_COURT: [
            r'\bappeal\b', r'\bcourt of appeal\b', r'\bpermission\b', r'\bca-\b',
            r'\bcivil division\b'
        ]
    }
    
    # Breach indicator patterns (expanded from statutory duties)
    BREACH_PATTERNS = {
        # Police breaches
        'POLICE_selective_investigation': [
            r'fail.* to investigate', r'ignored .* evidence', r'only investigated',
            r'didn.t consider', r'refused to', r'wouldn.t look at'
        ],
        'POLICE_disclosure_failure': [
            r'not disclosed', r'late disclosure', r'withheld', r'didn.t provide',
            r'failed to disclose'
        ],
        'POLICE_prejudice': [
            r'already decided', r'predetermined', r'made up .* mind',
            r'wouldn.t listen', r'dismissed .* account'
        ],
        
        # Local Authority breaches
        'LA_threshold_not_met': [
            r'no evidence of harm', r'threshold not met', r'no significant harm',
            r'not attributable', r'reasonable parent'
        ],
        'LA_no_candour': [
            r'didn.t disclose', r'withheld information', r'misleading',
            r'failed to inform', r'not told', r'wasn.t aware'
        ],
        'LA_disproportionate': [
            r'disproportionate', r'unnecessary', r'excessive', r'not necessary',
            r'didn.t need to', r'could have'
        ],
        'LA_no_plo': [
            r'no letter before', r'no pre-proceedings', r'without warning',
            r'emergency.*not emergency'
        ],
        
        # CAFCASS breaches
        'CAFCASS_not_independent': [
            r'adopted .* position', r'agreed with', r'followed .* without',
            r'didn.t question', r'accepted uncritically'
        ],
        'CAFCASS_no_child_voice': [
            r'didn.t see .* child', r'didn.t speak to', r'child.s wishes.*ignored',
            r'didn.t ask'
        ],
        'CAFCASS_one_sided': [
            r'only spoke to', r'didn.t interview', r'one parent',
            r'biased', r'one-sided'
        ],
        
        # Social Worker breaches
        'SW_prejudgment': [
            r'made up .* mind', r'already decided', r'predetermined',
            r'wouldn.t consider', r'refused to accept'
        ],
        'SW_inaccurate_recording': [
            r'not what .* said', r'misquoted', r'inaccurate', r'wrong',
            r'didn.t record', r'misrepresented'
        ],
        
        # Court breaches
        'COURT_no_fair_hearing': [
            r'wasn.t heard', r'didn.t allow', r'refused to consider',
            r'cut off', r'wouldn.t let', r'no opportunity'
        ],
        'COURT_no_reasons': [
            r'no reasons', r'didn.t explain', r'without reasons',
            r'no rationale'
        ],
        
        # Media breaches
        'MEDIA_identification': [
            r'identified', r'named', r'recogni[sz]able', r'published',
            r'filmed', r'broadcast'
        ]
    }
    
    def __init__(self, db_path: str):
        """Initialize the audit engine with database connection."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
    def run_full_audit(self, case_reference: str = None) -> AccountabilityReport:
        """
        Run complete accountability audit across all agencies.
        
        Args:
            case_reference: Optional case reference to filter by
            
        Returns:
            AccountabilityReport with all findings
        """
        # Load all claims and documents
        claims = self._load_claims(case_reference)
        documents = self._load_documents(case_reference)
        
        print(f"Analyzing {len(claims)} claims and {len(documents)} documents...")
        
        # Run audit for each agency
        agency_reports = {}
        total_breaches = 0
        critical_findings = []
        
        for agency in Agency:
            print(f"\n  Auditing {agency.value}...")
            report = self._audit_agency(agency, claims, documents)
            agency_reports[agency] = report
            total_breaches += report.total_breaches
            
            # Collect critical findings
            for breach in report.breaches:
                if breach.severity == BreachSeverity.CRITICAL:
                    critical_findings.append(
                        f"[{agency.value.upper()}] {breach.duty.title}: {breach.breach_indicator_matched}"
                    )
        
        # Generate recommended actions
        recommended_actions = self._generate_recommendations(agency_reports)
        
        return AccountabilityReport(
            case_reference=case_reference or "ALL_CASES",
            generated_at=datetime.now().isoformat(),
            agencies_analyzed=list(Agency),
            agency_reports=agency_reports,
            total_breaches=total_breaches,
            critical_findings=critical_findings,
            recommended_actions=recommended_actions
        )
    
    def _load_claims(self, case_reference: str = None) -> List[dict]:
        """Load claims from database."""
        cursor = self.conn.cursor()
        
        if case_reference:
            cursor.execute("""
                SELECT c.*, d.filename, d.title as doc_title, d.document_category,
                       ca.reference as case_ref
                FROM claims c
                LEFT JOIN documents d ON c.document_id = d.id
                LEFT JOIN cases ca ON c.case_id = ca.id
                WHERE ca.reference = ? OR c.case_id = ?
            """, (case_reference, case_reference))
        else:
            cursor.execute("""
                SELECT c.*, d.filename, d.title as doc_title, d.document_category,
                       ca.reference as case_ref
                FROM claims c
                LEFT JOIN documents d ON c.document_id = d.id
                LEFT JOIN cases ca ON c.case_id = ca.id
            """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _load_documents(self, case_reference: str = None) -> List[dict]:
        """Load documents from database."""
        cursor = self.conn.cursor()
        
        if case_reference:
            cursor.execute("""
                SELECT d.*, ca.reference as case_ref
                FROM documents d
                LEFT JOIN cases ca ON d.case_id = ca.id
                WHERE ca.reference = ? OR d.case_id = ?
            """, (case_reference, case_reference))
        else:
            cursor.execute("""
                SELECT d.*, ca.reference as case_ref
                FROM documents d
                LEFT JOIN cases ca ON d.case_id = ca.id
            """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _audit_agency(
        self, 
        agency: Agency, 
        claims: List[dict], 
        documents: List[dict]
    ) -> AgencyReport:
        """Audit a specific agency against its statutory duties."""
        
        # Filter content relevant to this agency
        relevant_claims = self._filter_by_agency(claims, agency)
        relevant_docs = self._filter_docs_by_agency(documents, agency)
        
        print(f"    Found {len(relevant_claims)} relevant claims, {len(relevant_docs)} relevant documents")
        
        # Check each statutory duty
        breaches = []
        duties = DUTIES_BY_AGENCY.get(agency, [])
        
        for duty in duties:
            duty_breaches = self._check_duty(duty, relevant_claims, relevant_docs)
            breaches.extend(duty_breaches)
        
        # Count by severity
        critical = sum(1 for b in breaches if b.severity == BreachSeverity.CRITICAL)
        serious = sum(1 for b in breaches if b.severity == BreachSeverity.SERIOUS)
        
        # Generate summary
        summary = self._generate_agency_summary(agency, breaches, len(relevant_claims))
        
        return AgencyReport(
            agency=agency,
            total_breaches=len(breaches),
            critical_breaches=critical,
            serious_breaches=serious,
            breaches=breaches,
            complaint_routes=get_complaint_routes().get(agency, []),
            summary=summary
        )
    
    def _filter_by_agency(self, claims: List[dict], agency: Agency) -> List[dict]:
        """Filter claims relevant to a specific agency."""
        keywords = self.AGENCY_KEYWORDS.get(agency, [])
        if not keywords:
            return claims
        
        pattern = '|'.join(keywords)
        relevant = []
        
        for claim in claims:
            text = (claim.get('claim_text') or '') + ' ' + (claim.get('context') or '')
            if re.search(pattern, text.lower()):
                relevant.append(claim)
        
        return relevant
    
    def _filter_docs_by_agency(self, documents: List[dict], agency: Agency) -> List[dict]:
        """Filter documents relevant to a specific agency."""
        keywords = self.AGENCY_KEYWORDS.get(agency, [])
        if not keywords:
            return documents
        
        pattern = '|'.join(keywords)
        relevant = []
        
        for doc in documents:
            text = (
                (doc.get('title') or '') + ' ' + 
                (doc.get('filename') or '') + ' ' +
                (doc.get('document_category') or '')
            )
            if re.search(pattern, text.lower()):
                relevant.append(doc)
        
        return relevant
    
    def _check_duty(
        self,
        duty: StatutoryDuty,
        claims: List[dict],
        documents: List[dict]
    ) -> List[IdentifiedBreach]:
        """Check for breaches of a specific duty."""
        breaches = []
        
        for indicator in duty.breach_indicators:
            # Create pattern from indicator
            indicator_pattern = self._indicator_to_pattern(indicator)
            
            # Search claims for evidence
            evidence = []
            for claim in claims:
                text = claim.get('claim_text', '')
                if re.search(indicator_pattern, text.lower()):
                    evidence.append(BreachEvidence(
                        document_id=claim.get('document_id', ''),
                        document_name=claim.get('filename') or claim.get('doc_title') or 'Unknown',
                        claim_id=claim.get('id'),
                        claim_text=text,
                        date=claim.get('date_made'),
                        author=claim.get('asserted_by'),
                        page_reference=str(claim.get('page_number', '')),
                        context=claim.get('context', '')
                    ))
            
            if evidence:
                breaches.append(IdentifiedBreach(
                    duty=duty,
                    breach_indicator_matched=indicator,
                    evidence=evidence,
                    analysis=f"Found {len(evidence)} instances of potential breach: {indicator}",
                    severity=duty.breach_severity,
                    complaint_ready=len(evidence) >= 2
                ))
        
        return breaches
    
    def _indicator_to_pattern(self, indicator: str) -> str:
        """Convert breach indicator to regex pattern."""
        # Escape special characters and create flexible pattern
        words = indicator.lower().split()
        pattern_parts = []
        
        for word in words:
            # Allow for variations
            if word in ['not', 'no', 'without', 'fail', 'failure', 'failing']:
                pattern_parts.append(r'(?:not|no|without|fail(?:ure|ing)?|didn.t|did not|hasn.t|haven.t)')
            else:
                # Allow word to appear with some flexibility
                pattern_parts.append(re.escape(word))
        
        return r'\b' + r'.{0,20}'.join(pattern_parts) + r'\b'
    
    def _generate_agency_summary(
        self, 
        agency: Agency, 
        breaches: List[IdentifiedBreach],
        total_claims: int
    ) -> str:
        """Generate summary for agency audit."""
        if not breaches:
            return f"No clear breaches identified for {agency.value}. {total_claims} relevant claims analyzed."
        
        critical = sum(1 for b in breaches if b.severity == BreachSeverity.CRITICAL)
        serious = sum(1 for b in breaches if b.severity == BreachSeverity.SERIOUS)
        
        return (
            f"{agency.value.upper()}: {len(breaches)} potential breaches identified from {total_claims} claims. "
            f"CRITICAL: {critical}, SERIOUS: {serious}. "
            f"Key issues: {', '.join(b.breach_indicator_matched for b in breaches[:3])}"
        )
    
    def _generate_recommendations(
        self, 
        agency_reports: Dict[Agency, AgencyReport]
    ) -> List[str]:
        """Generate recommended actions based on findings."""
        recommendations = []
        
        for agency, report in agency_reports.items():
            if report.critical_breaches > 0:
                routes = report.complaint_routes
                recommendations.append(
                    f"[{agency.value.upper()}] {report.critical_breaches} critical breaches - "
                    f"Recommend: {routes[0] if routes else 'Seek legal advice'}"
                )
        
        # Add general recommendations
        total_critical = sum(r.critical_breaches for r in agency_reports.values())
        if total_critical >= 3:
            recommendations.append(
                "CONSIDER: Judicial Review application - multiple systemic failures identified"
            )
        if total_critical >= 5:
            recommendations.append(
                "CONSIDER: Complaint to Parliamentary Ombudsman for maladministration"
            )
        
        # Check for Article 8 violations
        la_report = agency_reports.get(Agency.LOCAL_AUTHORITY)
        if la_report and la_report.critical_breaches >= 2:
            recommendations.append(
                "CONSIDER: Human Rights Act claim - potential Article 8 violations by Local Authority"
            )
        
        return recommendations
    
    def close(self):
        """Close database connection."""
        self.conn.close()


def run_accountability_audit(db_path: str, case_reference: str = None, output_file: str = None):
    """
    Run accountability audit and optionally save to file.
    
    Args:
        db_path: Path to database
        case_reference: Optional case to audit
        output_file: Optional output file for JSON report
    """
    engine = AccountabilityAuditEngine(db_path)
    
    try:
        report = engine.run_full_audit(case_reference)
        
        print("\n" + "="*70)
        print("ACCOUNTABILITY AUDIT REPORT")
        print("="*70)
        print(f"Case: {report.case_reference}")
        print(f"Generated: {report.generated_at}")
        print(f"Total Breaches Identified: {report.total_breaches}")
        
        print("\n" + "-"*70)
        print("CRITICAL FINDINGS")
        print("-"*70)
        for finding in report.critical_findings:
            print(f"  ⚠️  {finding}")
        
        print("\n" + "-"*70)
        print("AGENCY BREAKDOWN")
        print("-"*70)
        for agency, agency_report in report.agency_reports.items():
            if agency_report.total_breaches > 0:
                print(f"\n{agency.value.upper()}:")
                print(f"  Total: {agency_report.total_breaches} | Critical: {agency_report.critical_breaches} | Serious: {agency_report.serious_breaches}")
                print(f"  Complaint routes: {', '.join(agency_report.complaint_routes[:2])}")
        
        print("\n" + "-"*70)
        print("RECOMMENDED ACTIONS")
        print("-"*70)
        for i, action in enumerate(report.recommended_actions, 1):
            print(f"  {i}. {action}")
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"\nFull report saved to: {output_file}")
        
        return report
        
    finally:
        engine.close()


if __name__ == "__main__":
    # Run audit on the Phronesis database
    run_accountability_audit(
        db_path="Phronesis/data/db/phronesis.db",
        case_reference="PE23C50095",
        output_file="data/accountability_audit_report.json"
    )

