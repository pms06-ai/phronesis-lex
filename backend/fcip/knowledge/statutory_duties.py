"""
Comprehensive Statutory Duties Framework for Multi-Agency Accountability Audit.

This module defines the legal obligations of each agency involved in child protection
and family court proceedings, enabling systematic compliance checking.

Agencies covered:
1. Police (PACE 1984, Criminal Procedure Rules, College of Policing guidance)
2. Local Authority (Children Act 1989, Working Together 2023)
3. CAFCASS (Criminal Justice and Court Services Act 2000, Family Procedure Rules)
4. Social Workers (HCPC Standards, Social Workers Regulations 2018)
5. Family Court (Family Procedure Rules 2010, Practice Directions)
6. Media (Contempt of Court Act 1981, s.97 Children Act 1989)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class Agency(Enum):
    POLICE = "police"
    LOCAL_AUTHORITY = "local_authority"
    CAFCASS = "cafcass"
    SOCIAL_WORKER = "social_worker"
    FAMILY_COURT = "family_court"
    MEDIA = "media"
    APPEAL_COURT = "appeal_court"

class BreachSeverity(Enum):
    CRITICAL = "critical"      # Fundamental rights violation, grounds for judicial review
    SERIOUS = "serious"        # Significant procedural failure, complaint warranted
    MODERATE = "moderate"      # Notable deviation, should be documented
    MINOR = "minor"           # Technical breach, context dependent

@dataclass
class StatutoryDuty:
    """Represents a specific statutory duty or procedural requirement."""
    id: str
    agency: Agency
    title: str
    legal_basis: str  # e.g., "Children Act 1989 s.47"
    description: str
    requirements: List[str]
    breach_indicators: List[str]
    breach_severity: BreachSeverity
    complaint_route: str
    relevant_case_law: List[str] = field(default_factory=list)
    time_limits: Optional[str] = None


# ============================================================================
# POLICE STATUTORY DUTIES
# ============================================================================

POLICE_DUTIES = [
    StatutoryDuty(
        id="POLICE_001",
        agency=Agency.POLICE,
        title="Duty to Investigate Without Prejudice",
        legal_basis="PACE 1984; College of Policing Authorised Professional Practice",
        description="Police must conduct investigations objectively, gathering evidence that both supports and undermines the prosecution case.",
        requirements=[
            "Gather all relevant evidence regardless of which party it supports",
            "Document exculpatory evidence in disclosure schedules",
            "Interview suspects fairly under PACE Code C",
            "Not allow external pressures to influence investigation",
            "Review decisions when new evidence emerges"
        ],
        breach_indicators=[
            "Failure to investigate alternative suspects",
            "Selective disclosure of evidence",
            "Leading questions in interviews",
            "Ignoring exculpatory evidence",
            "Delaying investigation without justification",
            "Making public statements prejudging guilt"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="IOPC (Independent Office for Police Conduct) or internal Professional Standards Department",
        relevant_case_law=[
            "R v Ward [1993] - duty to disclose",
            "R v Kiszko - wrongful conviction due to non-disclosure"
        ]
    ),
    StatutoryDuty(
        id="POLICE_002",
        agency=Agency.POLICE,
        title="PACE Code C - Treatment of Suspects",
        legal_basis="Police and Criminal Evidence Act 1984, Code C",
        description="Suspects must be treated fairly during detention and interview.",
        requirements=[
            "Right to legal representation before and during interview",
            "Right to have someone informed of arrest",
            "Adequate rest periods between interviews",
            "Accurate recording of interviews",
            "Caution must be properly administered",
            "Vulnerable suspects require appropriate adult"
        ],
        breach_indicators=[
            "Interview without solicitor when requested",
            "Excessive interview duration",
            "Failure to offer breaks",
            "Tampering with interview records",
            "Oppressive questioning"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="IOPC; Evidence may be excluded under s.78 PACE",
        relevant_case_law=[
            "R v Samuel [1988] - right to solicitor",
            "R v Paris (1993) - oppressive interviews"
        ]
    ),
    StatutoryDuty(
        id="POLICE_003",
        agency=Agency.POLICE,
        title="Pre-Charge Bail Conditions",
        legal_basis="PACE 1984 s.47ZA-ZL (as amended by Policing and Crime Act 2017)",
        description="Bail conditions must be necessary and proportionate.",
        requirements=[
            "Bail conditions must be necessary for specified purposes",
            "Conditions must be proportionate to circumstances",
            "Regular review of bail necessity",
            "Timely investigation to avoid extended bail",
            "Court oversight for extensions beyond 9 months"
        ],
        breach_indicators=[
            "Excessive bail conditions not justified",
            "Failure to review bail regularly",
            "Unreasonable delays in investigation",
            "Bail used as punishment before conviction"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Application to vary bail; complaint to PSD",
        time_limits="Initial 3 months, extensions require senior officer/court approval"
    ),
    StatutoryDuty(
        id="POLICE_004",
        agency=Agency.POLICE,
        title="Disclosure Duty",
        legal_basis="Criminal Procedure and Investigations Act 1996; Attorney General Guidelines",
        description="Police must disclose all material that might undermine prosecution or assist defence.",
        requirements=[
            "Schedule all unused material",
            "Identify material meeting disclosure test",
            "Continuing duty throughout proceedings",
            "Third party material must be pursued",
            "Sensitive material requires court application"
        ],
        breach_indicators=[
            "Failure to schedule relevant material",
            "Late disclosure causing prejudice",
            "Destruction of potentially relevant material",
            "Misleading disclosure schedules"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Defence application to court; IOPC for misconduct",
        relevant_case_law=[
            "R v H & C [2004] - PII procedure",
            "R v Nunn [2015] - continuing duty"
        ]
    ),
]

# ============================================================================
# LOCAL AUTHORITY STATUTORY DUTIES
# ============================================================================

LOCAL_AUTHORITY_DUTIES = [
    StatutoryDuty(
        id="LA_001",
        agency=Agency.LOCAL_AUTHORITY,
        title="Section 47 Investigation Duty",
        legal_basis="Children Act 1989 s.47",
        description="Where LA has reasonable cause to suspect child is suffering or likely to suffer significant harm, must investigate.",
        requirements=[
            "Make enquiries to decide whether action needed",
            "See the child (unless satisfied not required)",
            "Decide what action if any to take",
            "Conclude within 45 working days",
            "Multi-agency coordination"
        ],
        breach_indicators=[
            "Failure to investigate notified concerns",
            "Not seeing the child",
            "Exceeding 45-day timeline without justification",
            "Single-agency approach ignoring partner information",
            "Inadequate assessment of risk"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Local Authority complaints procedure; LGSCO (Local Government & Social Care Ombudsman)",
        time_limits="Initial assessment within 45 working days"
    ),
    StatutoryDuty(
        id="LA_002",
        agency=Agency.LOCAL_AUTHORITY,
        title="Care Proceedings Threshold",
        legal_basis="Children Act 1989 s.31(2)",
        description="Court may only make care/supervision order if threshold criteria met.",
        requirements=[
            "Child suffering or likely to suffer significant harm",
            "Harm attributable to care given or likely to be given",
            "Care not what reasonable parent would give",
            "OR child beyond parental control",
            "Must prove on balance of probabilities"
        ],
        breach_indicators=[
            "Issuing proceedings without evidence meeting threshold",
            "Conflating concern with significant harm",
            "Failure to evidence attributability to parent's care",
            "Using care proceedings as tool when voluntary measures appropriate"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Challenge in proceedings; judicial review of decision to issue",
        relevant_case_law=[
            "Re B [2013] UKSC - significant harm test",
            "Re J [2013] - likelihood of harm",
            "Lancashire CC v B [2000] - attributability"
        ]
    ),
    StatutoryDuty(
        id="LA_003",
        agency=Agency.LOCAL_AUTHORITY,
        title="Duty of Candour",
        legal_basis="Working Together 2023; Re W (Children) [2014]",
        description="LA must present all relevant information to court, including that which undermines its case.",
        requirements=[
            "Disclose all relevant documents",
            "Present balanced social work assessments",
            "Acknowledge weaknesses in own case",
            "Update court promptly on changed circumstances",
            "Not mislead court by omission"
        ],
        breach_indicators=[
            "Selective presentation of evidence",
            "Withholding exculpatory material",
            "Biased social work reports",
            "Failure to disclose material changes",
            "Continuing proceedings when threshold no longer met"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Raise in proceedings; professional conduct complaint; LGSCO",
        relevant_case_law=[
            "Re W (Children) [2014] - duty of candour",
            "Re C and B [2001] - local authority obligations"
        ]
    ),
    StatutoryDuty(
        id="LA_004",
        agency=Agency.LOCAL_AUTHORITY,
        title="No Order Principle",
        legal_basis="Children Act 1989 s.1(5)",
        description="Court shall not make order unless doing so is better for child than making no order.",
        requirements=[
            "Consider whether order necessary",
            "Evidence that order will improve child's situation",
            "Not use orders as 'insurance' without necessity",
            "Proportionality assessment"
        ],
        breach_indicators=[
            "Seeking orders without clear benefit",
            "Failing to evidence why order needed",
            "Disproportionate orders sought"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Challenge in proceedings",
        relevant_case_law=[
            "Re G (Children) [2006] - necessity test"
        ]
    ),
    StatutoryDuty(
        id="LA_005",
        agency=Agency.LOCAL_AUTHORITY,
        title="Article 8 ECHR - Right to Family Life",
        legal_basis="Human Rights Act 1998; ECHR Article 8",
        description="Any interference with family life must be lawful, necessary and proportionate.",
        requirements=[
            "In accordance with law",
            "Pursuing legitimate aim",
            "Necessary in democratic society",
            "Proportionate to aim pursued",
            "Less intrusive measures considered first"
        ],
        breach_indicators=[
            "Removing children without proper legal basis",
            "Failing to consider kinship care",
            "Disproportionate restrictions on contact",
            "Not actively supporting family reunification",
            "Seeking adoption without exploring alternatives"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Raise in proceedings; application to ECtHR",
        relevant_case_law=[
            "YC v United Kingdom [2012] - proportionality",
            "Re B-S [2013] - proper analysis required"
        ]
    ),
    StatutoryDuty(
        id="LA_006",
        agency=Agency.LOCAL_AUTHORITY,
        title="PLO Pre-Proceedings Requirements",
        legal_basis="Public Law Outline 2014; Practice Direction 12A",
        description="Before issuing care proceedings, LA must follow pre-proceedings protocol.",
        requirements=[
            "Letter Before Proceedings to parents",
            "Offer of legal advice/representation",
            "Pre-proceedings meeting",
            "Family Group Conference considered",
            "Kinship assessment if appropriate"
        ],
        breach_indicators=[
            "Issuing without pre-proceedings letter",
            "Not offering legal advice",
            "Failing to hold pre-proceedings meeting",
            "Not considering family solutions",
            "Emergency proceedings when not emergency"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Challenge timetable in proceedings; complaint to LA",
        time_limits="Pre-proceedings should allow reasonable time for response"
    ),
]

# ============================================================================
# CAFCASS STATUTORY DUTIES
# ============================================================================

CAFCASS_DUTIES = [
    StatutoryDuty(
        id="CAFCASS_001",
        agency=Agency.CAFCASS,
        title="Independence and Impartiality",
        legal_basis="Criminal Justice and Court Services Act 2000 s.12; CAFCASS Operating Framework",
        description="CAFCASS officers must act independently and impartially, representing child's interests.",
        requirements=[
            "Independent of all parties including LA",
            "Child-focused assessment",
            "No predetermined conclusions",
            "Consider all relevant evidence",
            "Balanced analysis of options"
        ],
        breach_indicators=[
            "Adopting LA position without independent analysis",
            "Dismissing parent's evidence without fair consideration",
            "Confirmation bias in assessments",
            "Failure to meet with all relevant parties",
            "Predetermined recommendations"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="CAFCASS complaints procedure; Parliamentary Ombudsman",
        relevant_case_law=[
            "Re S (A Child) [2014] - guardian's duties"
        ]
    ),
    StatutoryDuty(
        id="CAFCASS_002",
        agency=Agency.CAFCASS,
        title="Section 7 Report Requirements",
        legal_basis="Children Act 1989 s.7; Family Procedure Rules 2010",
        description="When directed, CAFCASS must prepare report on child's welfare.",
        requirements=[
            "Analysis of welfare checklist factors",
            "Interview with child (age appropriate)",
            "Interview with both parents",
            "Consider relevant third parties",
            "Clear reasoned recommendations"
        ],
        breach_indicators=[
            "Not seeing the child",
            "Only interviewing one parent",
            "Superficial analysis",
            "Recommendations not supported by evidence",
            "Excessive delay in reporting"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="CAFCASS complaints; raise concerns with court",
        time_limits="As directed by court, typically 12-16 weeks"
    ),
    StatutoryDuty(
        id="CAFCASS_003",
        agency=Agency.CAFCASS,
        title="Rule 16.4 Guardian Duties",
        legal_basis="Family Procedure Rules 2010 r.16.4",
        description="Children's Guardian appointed in specified proceedings has enhanced duties.",
        requirements=[
            "Appoint solicitor for child",
            "Instruct solicitor on child's behalf",
            "Advise court on child's interests",
            "File guardian's report",
            "Attend all hearings"
        ],
        breach_indicators=[
            "Delay in appointing solicitor",
            "Not filing reports as directed",
            "Absence from hearings without good reason",
            "Failing to represent child's ascertainable wishes"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="CAFCASS complaints; inform court of concerns"
    ),
    StatutoryDuty(
        id="CAFCASS_004",
        agency=Agency.CAFCASS,
        title="Duty to Ascertain Child's Wishes",
        legal_basis="Children Act 1989 s.1(3)(a); UNCRC Article 12",
        description="Must ascertain and convey child's wishes and feelings to court.",
        requirements=[
            "See child alone (age appropriate)",
            "Use appropriate communication methods",
            "Record child's views accurately",
            "Distinguish child's wishes from guardian's recommendation",
            "Explain if recommending against child's wishes"
        ],
        breach_indicators=[
            "Not meeting child",
            "Not reporting child's actual wishes",
            "Conflating child's wishes with guardian's view",
            "Age-inappropriate interviewing",
            "Failure to use interpreters/intermediaries when needed"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="CAFCASS complaints; challenge report in proceedings"
    ),
]

# ============================================================================
# SOCIAL WORKER PROFESSIONAL DUTIES
# ============================================================================

SOCIAL_WORKER_DUTIES = [
    StatutoryDuty(
        id="SW_001",
        agency=Agency.SOCIAL_WORKER,
        title="HCPC Standards of Proficiency",
        legal_basis="Health and Care Professions Council Standards of Proficiency; Social Workers Regulations 2018",
        description="Social workers must maintain professional standards set by HCPC.",
        requirements=[
            "Be able to practise safely and effectively",
            "Be able to practise within legal and ethical boundaries",
            "Maintain fitness to practise",
            "Be able to communicate effectively",
            "Be able to reflect on and review practice"
        ],
        breach_indicators=[
            "Acting outside competence",
            "Failing to follow legal requirements",
            "Poor record keeping",
            "Inadequate communication with families",
            "Defensive practice without reflection"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="HCPC Fitness to Practise; employer disciplinary process"
    ),
    StatutoryDuty(
        id="SW_002",
        agency=Agency.SOCIAL_WORKER,
        title="Professional Boundaries",
        legal_basis="HCPC Standards of Conduct; BASW Code of Ethics",
        description="Must maintain appropriate professional boundaries.",
        requirements=[
            "Impartial assessment",
            "No personal relationships with service users",
            "Declare conflicts of interest",
            "Professional conduct in all interactions",
            "Appropriate use of authority"
        ],
        breach_indicators=[
            "Pre-judging cases before assessment",
            "Personal animosity affecting decisions",
            "Undeclared conflicts of interest",
            "Inappropriate communications",
            "Misuse of professional authority"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="HCPC; employer; LGSCO if affects service"
    ),
    StatutoryDuty(
        id="SW_003",
        agency=Agency.SOCIAL_WORKER,
        title="Accurate Recording",
        legal_basis="Working Together 2023; HCPC Standards",
        description="Must maintain accurate, timely and clear records.",
        requirements=[
            "Contemporaneous recording",
            "Distinguish fact from opinion",
            "Record decisions and rationale",
            "Accurate attribution of statements",
            "Accessible to service users"
        ],
        breach_indicators=[
            "Delayed recording",
            "Opinion presented as fact",
            "Missing decision rationale",
            "Misattributing statements",
            "Records not shared appropriately"
        ],
        breach_severity=BreachSeverity.MODERATE,
        complaint_route="Employer; HCPC if pattern of poor practice"
    ),
    StatutoryDuty(
        id="SW_004",
        agency=Agency.SOCIAL_WORKER,
        title="Anti-Oppressive Practice",
        legal_basis="BASW Code of Ethics; Equality Act 2010",
        description="Must practice in anti-oppressive, non-discriminatory manner.",
        requirements=[
            "Recognise and address power imbalances",
            "Challenge discrimination",
            "Cultural competence",
            "Avoid stereotyping",
            "Promote equality"
        ],
        breach_indicators=[
            "Discriminatory language in records",
            "Stereotyping based on protected characteristics",
            "Failing to provide interpretation services",
            "Cultural assumptions affecting assessment",
            "Not addressing family's concerns about discrimination"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Employer; HCPC; Equality and Human Rights Commission if discrimination"
    ),
]

# ============================================================================
# FAMILY COURT PROCEDURAL DUTIES
# ============================================================================

COURT_DUTIES = [
    StatutoryDuty(
        id="COURT_001",
        agency=Agency.FAMILY_COURT,
        title="Article 6 ECHR - Fair Trial",
        legal_basis="Human Rights Act 1998; ECHR Article 6",
        description="Every party entitled to fair hearing within reasonable time by independent tribunal.",
        requirements=[
            "Reasonable time for preparation",
            "Access to evidence",
            "Opportunity to present case",
            "Reasoned judgment",
            "Independent and impartial tribunal"
        ],
        breach_indicators=[
            "Inadequate time to respond to evidence",
            "Non-disclosure of relevant material",
            "Not allowing party to be heard",
            "Judgment without reasons",
            "Apparent bias"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Appeal; Judicial Conduct Investigations Office (JCIO)",
        relevant_case_law=[
            "Re K and H [2007] - fair hearing",
            "Re G [2014] - reasons for judgment"
        ]
    ),
    StatutoryDuty(
        id="COURT_002",
        agency=Agency.FAMILY_COURT,
        title="Overriding Objective",
        legal_basis="Family Procedure Rules 2010 r.1.1",
        description="Court must deal with cases justly, having regard to welfare issues involved.",
        requirements=[
            "Ensure parties on equal footing",
            "Save expense",
            "Deal proportionately",
            "Deal expeditiously and fairly",
            "Allot appropriate share of court resources"
        ],
        breach_indicators=[
            "Unequal treatment of parties",
            "Disproportionate costs orders",
            "Unreasonable delays",
            "Refusing to list urgent applications",
            "Inadequate case management"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Appeal; complaint to court manager; JCIO for judicial conduct"
    ),
    StatutoryDuty(
        id="COURT_003",
        agency=Agency.FAMILY_COURT,
        title="Welfare Checklist Application",
        legal_basis="Children Act 1989 s.1(3)",
        description="Court must have regard to welfare checklist in contested s.8 and Part IV proceedings.",
        requirements=[
            "Consider all checklist factors",
            "Ascertainable wishes of child",
            "Physical, emotional, educational needs",
            "Likely effect of change",
            "Age, sex, background, characteristics",
            "Any harm suffered or at risk of",
            "Capability of parents",
            "Range of powers available"
        ],
        breach_indicators=[
            "Not addressing all factors",
            "Ignoring child's wishes without explanation",
            "Superficial analysis",
            "Not considering range of powers"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Appeal on grounds judgment failed to apply checklist"
    ),
    StatutoryDuty(
        id="COURT_004",
        agency=Agency.FAMILY_COURT,
        title="Practice Direction 12J - Domestic Abuse",
        legal_basis="FPR 2010 Practice Direction 12J",
        description="Court must consider domestic abuse allegations and their impact.",
        requirements=[
            "Identify abuse allegations at first hearing",
            "Consider whether fact-finding needed",
            "Apply appropriate case management",
            "Consider safety of parties and child",
            "Scott Schedule if contested allegations"
        ],
        breach_indicators=[
            "Ignoring domestic abuse allegations",
            "Refusing fact-finding without reasons",
            "Inadequate protection measures",
            "Treating allegations as dispute rather than safeguarding"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Appeal; JCIO for judicial conduct",
        relevant_case_law=[
            "Re H-N [2021] - proper approach to PD12J"
        ]
    ),
]

# ============================================================================
# MEDIA DUTIES (Channel 4)
# ============================================================================

MEDIA_DUTIES = [
    StatutoryDuty(
        id="MEDIA_001",
        agency=Agency.MEDIA,
        title="Section 97 Children Act - Publication Restrictions",
        legal_basis="Children Act 1989 s.97",
        description="Criminal offence to publish material identifying child in family proceedings.",
        requirements=[
            "Not identify child involved in proceedings",
            "Not publish information leading to identification",
            "Court permission required for any publication"
        ],
        breach_indicators=[
            "Publishing identifying information",
            "Filming in court precincts",
            "Publishing without court permission",
            "Material allowing jigsaw identification"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Ofcom; contempt of court application; police",
        relevant_case_law=[
            "Re S [2004] - balancing Article 8 and 10"
        ]
    ),
    StatutoryDuty(
        id="MEDIA_002",
        agency=Agency.MEDIA,
        title="Contempt of Court",
        legal_basis="Contempt of Court Act 1981",
        description="Publications creating substantial risk of serious prejudice may be contempt.",
        requirements=[
            "Not prejudice active proceedings",
            "Strict liability for publications",
            "Verify proceedings are not active before publication"
        ],
        breach_indicators=[
            "Publishing during active proceedings",
            "Material prejudging outcome",
            "Pressure on witnesses or parties"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Attorney General; contempt application to court"
    ),
    StatutoryDuty(
        id="MEDIA_003",
        agency=Agency.MEDIA,
        title="Ofcom Broadcasting Code",
        legal_basis="Communications Act 2003; Ofcom Broadcasting Code",
        description="Broadcasters must comply with Ofcom standards on fairness, privacy, harm.",
        requirements=[
            "Informed consent for participation",
            "Fair treatment of contributors",
            "Privacy protections",
            "Accuracy in factual programmes",
            "Not materially misleading"
        ],
        breach_indicators=[
            "Consent obtained under pressure or misrepresentation",
            "Unfair editing",
            "Unwarranted privacy infringement",
            "Factual inaccuracies",
            "One-sided presentation"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Ofcom complaint; legal action for defamation/privacy"
    ),
]

# ============================================================================
# APPEAL COURT DUTIES
# ============================================================================

APPEAL_COURT_DUTIES = [
    StatutoryDuty(
        id="APPEAL_001",
        agency=Agency.APPEAL_COURT,
        title="Permission to Appeal Criteria",
        legal_basis="CPR 52.6; FPR 30.3",
        description="Permission required for appeal; granted if real prospect of success or other compelling reason.",
        requirements=[
            "Consider whether real prospect of success",
            "Consider if other compelling reason",
            "Give reasons for refusal",
            "Consider if oral hearing needed"
        ],
        breach_indicators=[
            "Refusing without adequate reasons",
            "Failing to identify arguable grounds",
            "Not considering compelling reason criterion"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Renewed application; JCIO for judicial conduct"
    ),
]


# ============================================================================
# COMPILE ALL DUTIES
# ============================================================================

ALL_STATUTORY_DUTIES = (
    POLICE_DUTIES + 
    LOCAL_AUTHORITY_DUTIES + 
    CAFCASS_DUTIES + 
    SOCIAL_WORKER_DUTIES + 
    COURT_DUTIES + 
    MEDIA_DUTIES +
    APPEAL_COURT_DUTIES
)

DUTIES_BY_AGENCY = {
    Agency.POLICE: POLICE_DUTIES,
    Agency.LOCAL_AUTHORITY: LOCAL_AUTHORITY_DUTIES,
    Agency.CAFCASS: CAFCASS_DUTIES,
    Agency.SOCIAL_WORKER: SOCIAL_WORKER_DUTIES,
    Agency.FAMILY_COURT: COURT_DUTIES,
    Agency.MEDIA: MEDIA_DUTIES,
    Agency.APPEAL_COURT: APPEAL_COURT_DUTIES,
}

def get_duties_for_agency(agency: Agency) -> List[StatutoryDuty]:
    """Get all statutory duties for a specific agency."""
    return DUTIES_BY_AGENCY.get(agency, [])

def get_all_breach_indicators() -> Dict[str, List[str]]:
    """Get all breach indicators indexed by duty ID."""
    return {duty.id: duty.breach_indicators for duty in ALL_STATUTORY_DUTIES}

def get_complaint_routes() -> Dict[Agency, List[str]]:
    """Get complaint routes for each agency."""
    routes = {}
    for agency in Agency:
        routes[agency] = list(set(
            duty.complaint_route for duty in get_duties_for_agency(agency)
        ))
    return routes

