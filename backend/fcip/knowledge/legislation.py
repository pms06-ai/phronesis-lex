"""
FCIP Legal Knowledge Base - Primary and Secondary Legislation

Comprehensive UK family law legislation database for multi-agency audit.
Covers: Police, Local Authority, CAFCASS, Social Workers, Family Court, 
Appeal Court, and Media involvement.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class Agency(str, Enum):
    """Agencies subject to audit."""
    POLICE = "police"
    LOCAL_AUTHORITY = "local_authority"
    CAFCASS = "cafcass"
    SOCIAL_WORKER = "social_worker"
    FAMILY_COURT = "family_court"
    APPEAL_COURT = "appeal_court"
    MEDIA = "media"
    SOLICITOR = "solicitor"
    BARRISTER = "barrister"
    EXPERT_WITNESS = "expert_witness"
    JUDGE = "judge"


class ViolationType(str, Enum):
    """Types of procedural/legal violations."""
    STATUTORY_DUTY = "statutory_duty"
    PROCEDURAL = "procedural"
    HUMAN_RIGHTS = "human_rights"
    PROFESSIONAL_STANDARDS = "professional_standards"
    GUIDANCE_BREACH = "guidance_breach"
    CASE_LAW = "case_law"
    DATA_PROTECTION = "data_protection"
    CONTEMPT = "contempt"


@dataclass
class LegislativeProvision:
    """A specific provision from legislation."""
    provision_id: str
    act: str
    section: str
    subsection: Optional[str] = None
    title: str = ""
    text: str = ""
    duty_bearer: List[Agency] = field(default_factory=list)
    duty_type: str = ""  # "duty", "power", "prohibition"
    enforceable: bool = True
    penalty: Optional[str] = None
    linked_guidance: List[str] = field(default_factory=list)
    linked_cases: List[str] = field(default_factory=list)


# =============================================================================
# CHILDREN ACT 1989 - Core child protection legislation
# =============================================================================

CHILDREN_ACT_1989 = {
    # PART I - INTRODUCTORY
    "CA1989.s1.1": LegislativeProvision(
        provision_id="CA1989.s1.1",
        act="Children Act 1989",
        section="1",
        subsection="1",
        title="Paramountcy Principle",
        text="""When a court determines any question with respect to—
(a) the upbringing of a child; or
(b) the administration of a child's property or the application of any income arising from it,
the child's welfare shall be the court's paramount consideration.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.JUDGE],
        duty_type="duty",
        linked_cases=["Re_G_2006", "Re_B_2009", "Re_W_2016"],
    ),
    
    "CA1989.s1.2": LegislativeProvision(
        provision_id="CA1989.s1.2",
        act="Children Act 1989",
        section="1",
        subsection="2",
        title="No Delay Principle",
        text="""In any proceedings in which any question with respect to the upbringing of a child arises, 
the court shall have regard to the general principle that any delay in determining the question 
is likely to prejudice the welfare of the child.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.JUDGE, Agency.LOCAL_AUTHORITY, Agency.CAFCASS],
        duty_type="duty",
        linked_guidance=["FPR_2010_r1.1", "PLO_2014"],
    ),
    
    "CA1989.s1.2A": LegislativeProvision(
        provision_id="CA1989.s1.2A",
        act="Children Act 1989",
        section="1",
        subsection="2A",
        title="26 Week Time Limit",
        text="""A court... is to draw up a timetable with a view to disposing of the application—
(a) without delay, and
(b) in any event within twenty-six weeks beginning with the day on which the application was issued.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.JUDGE],
        duty_type="duty",
    ),
    
    "CA1989.s1.3": LegislativeProvision(
        provision_id="CA1989.s1.3",
        act="Children Act 1989",
        section="1",
        subsection="3",
        title="Welfare Checklist",
        text="""In the circumstances mentioned in subsection (4), a court shall have regard in particular to—
(a) the ascertainable wishes and feelings of the child concerned (considered in the light of his age and understanding);
(b) his physical, emotional and educational needs;
(c) the likely effect on him of any change in his circumstances;
(d) his age, sex, background and any characteristics of his which the court considers relevant;
(e) any harm which he has suffered or is at risk of suffering;
(f) how capable each of his parents, and any other person in relation to whom the court considers the question to be relevant, is of meeting his needs;
(g) the range of powers available to the court under this Act in the proceedings in question.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.JUDGE, Agency.CAFCASS],
        duty_type="duty",
        linked_cases=["Re_B_2009", "Re_W_2016", "Re_A_2015"],
    ),
    
    "CA1989.s1.5": LegislativeProvision(
        provision_id="CA1989.s1.5",
        act="Children Act 1989",
        section="1",
        subsection="5",
        title="No Order Principle",
        text="""Where a court is considering whether or not to make one or more orders under this Act with respect to a child, 
it shall not make the order or any of the orders unless it considers that doing so would be 
better for the child than making no order at all.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.JUDGE],
        duty_type="duty",
        linked_cases=["Re_B_2009"],
    ),
    
    # PART III - LOCAL AUTHORITY SUPPORT
    "CA1989.s17.1": LegislativeProvision(
        provision_id="CA1989.s17.1",
        act="Children Act 1989",
        section="17",
        subsection="1",
        title="General Duty to Children in Need",
        text="""It shall be the general duty of every local authority—
(a) to safeguard and promote the welfare of children within their area who are in need; and
(b) so far as is consistent with that duty, to promote the upbringing of such children by their families,
by providing a range and level of services appropriate to those children's needs.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY],
        duty_type="duty",
        linked_guidance=["Working_Together_2023"],
    ),
    
    "CA1989.s20.1": LegislativeProvision(
        provision_id="CA1989.s20.1",
        act="Children Act 1989",
        section="20",
        subsection="1",
        title="Accommodation for Children",
        text="""Every local authority shall provide accommodation for any child in need within their area who appears to them to require accommodation as a result of—
(a) there being no person who has parental responsibility for him;
(b) his being lost or having been abandoned; or
(c) the person who has been caring for him being prevented (whether or not permanently, and for whatever reason) from providing him with suitable accommodation or care.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY],
        duty_type="duty",
    ),
    
    "CA1989.s20.7": LegislativeProvision(
        provision_id="CA1989.s20.7",
        act="Children Act 1989",
        section="20",
        subsection="7",
        title="Parental Objection to S20",
        text="""A local authority may not provide accommodation under this section for any child if any person who—
(a) has parental responsibility for him; and
(b) is willing and able to—
(i) provide accommodation for him; or
(ii) arrange for accommodation to be provided for him,
objects.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY],
        duty_type="prohibition",
        linked_cases=["Re_N_2015", "Williams_v_Hackney_2018"],
    ),
    
    "CA1989.s20.8": LegislativeProvision(
        provision_id="CA1989.s20.8",
        act="Children Act 1989",
        section="20",
        subsection="8",
        title="S20 Removal by Parent",
        text="""Any person who has parental responsibility for a child may at any time remove the child 
from accommodation provided by or on behalf of the local authority under this section.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY],
        duty_type="duty",
    ),
    
    # PART IV - CARE AND SUPERVISION
    "CA1989.s31.2": LegislativeProvision(
        provision_id="CA1989.s31.2",
        act="Children Act 1989",
        section="31",
        subsection="2",
        title="Threshold Criteria",
        text="""A court may only make a care order or supervision order if it is satisfied—
(a) that the child concerned is suffering, or is likely to suffer, significant harm; and
(b) that the harm, or likelihood of harm, is attributable to—
(i) the care given to the child, or likely to be given to him if the order were not made, not being what it would be reasonable to expect a parent to give to him; or
(ii) the child's being beyond parental control.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.JUDGE, Agency.LOCAL_AUTHORITY],
        duty_type="duty",
        linked_cases=["Re_B_2008", "Re_J_2013", "Lancashire_v_B_2000"],
    ),
    
    "CA1989.s31.9": LegislativeProvision(
        provision_id="CA1989.s31.9",
        act="Children Act 1989",
        section="31",
        subsection="9",
        title="Definition of Harm",
        text=""""harm" means ill-treatment or the impairment of health or development including, for example, 
impairment suffered from seeing or hearing the ill-treatment of another;
"development" means physical, intellectual, emotional, social or behavioural development;
"health" means physical or mental health; and
"ill-treatment" includes sexual abuse and forms of ill-treatment which are not physical.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.LOCAL_AUTHORITY, Agency.CAFCASS],
        duty_type="definition",
    ),
    
    "CA1989.s31.10": LegislativeProvision(
        provision_id="CA1989.s31.10",
        act="Children Act 1989",
        section="31",
        subsection="10",
        title="Significant Harm Comparison",
        text="""Where the question of whether harm suffered by a child is significant turns on the child's health or development, 
his health or development shall be compared with that which could reasonably be expected of a similar child.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.LOCAL_AUTHORITY],
        duty_type="duty",
    ),
    
    "CA1989.s38.6": LegislativeProvision(
        provision_id="CA1989.s38.6",
        act="Children Act 1989",
        section="38",
        subsection="6",
        title="Interim Care Order Assessments",
        text="""Where the court makes an interim care order, or interim supervision order, it may give such directions 
(if any) as it considers appropriate with regard to the medical or psychiatric examination or other 
assessment of the child.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.JUDGE],
        duty_type="power",
        linked_cases=["Re_G_2020"],
    ),
    
    # PART V - PROTECTION OF CHILDREN  
    "CA1989.s44.1": LegislativeProvision(
        provision_id="CA1989.s44.1",
        act="Children Act 1989",
        section="44",
        subsection="1",
        title="Emergency Protection Orders",
        text="""Where any person ("the applicant") applies to the court for an order to be made under this section 
with respect to a child, the court may make the order if, but only if, it is satisfied that—
(a) there is reasonable cause to believe that the child is likely to suffer significant harm if—
(i) he is not removed to accommodation provided by or on behalf of the applicant; or
(ii) he does not remain in the place in which he is then being accommodated.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.LOCAL_AUTHORITY, Agency.POLICE],
        duty_type="power",
    ),
    
    "CA1989.s46.1": LegislativeProvision(
        provision_id="CA1989.s46.1",
        act="Children Act 1989",
        section="46",
        subsection="1",
        title="Police Protection",
        text="""Where a constable has reasonable cause to believe that a child would otherwise be likely to suffer 
significant harm, he may—
(a) remove the child to suitable accommodation and keep him there; or
(b) take such steps as are reasonable to ensure that the child's removal from any hospital, 
or other place, in which he is then being accommodated is prevented.""",
        duty_bearer=[Agency.POLICE],
        duty_type="power",
        linked_guidance=["PACE_1984", "College_of_Policing_APP"],
    ),
    
    "CA1989.s46.3": LegislativeProvision(
        provision_id="CA1989.s46.3",
        act="Children Act 1989",
        section="46",
        subsection="3",
        title="Police Protection Duration",
        text="""No child may be kept in police protection for more than 72 hours.""",
        duty_bearer=[Agency.POLICE],
        duty_type="prohibition",
    ),
    
    "CA1989.s47.1": LegislativeProvision(
        provision_id="CA1989.s47.1",
        act="Children Act 1989",
        section="47",
        subsection="1",
        title="Duty to Investigate",
        text="""Where a local authority—
(a) are informed that a child who lives, or is found, in their area—
(i) is the subject of an emergency protection order; or
(ii) is in police protection; or
(b) have reasonable cause to suspect that a child who lives, or is found, in their area is suffering, 
or is likely to suffer, significant harm,
the authority shall make, or cause to be made, such enquiries as they consider necessary to enable 
them to decide whether they should take any action to safeguard or promote the child's welfare.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY],
        duty_type="duty",
        linked_guidance=["Working_Together_2023"],
    ),
    
    "CA1989.s47.9": LegislativeProvision(
        provision_id="CA1989.s47.9",
        act="Children Act 1989",
        section="47",
        subsection="9",
        title="Multi-Agency Cooperation",
        text="""Where a local authority are conducting enquiries under this section, it shall be the duty of any person 
mentioned in subsection (11) to assist them with those enquiries (in particular by providing relevant 
information and advice) if called upon by the authority to do so.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY, Agency.POLICE, Agency.CAFCASS],
        duty_type="duty",
    ),
    
    "CA1989.s47.11": LegislativeProvision(
        provision_id="CA1989.s47.11",
        act="Children Act 1989",
        section="47",
        subsection="11",
        title="Persons Required to Assist",
        text="""The persons are—
(a) any local authority;
(b) any local education authority;
(c) any local housing authority;
(d) any clinical commissioning group, Local Health Board, Special Health Authority, 
NHS trust or NHS foundation trust; and
(e) any person authorised by the Secretary of State for the purposes of this section.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY, Agency.POLICE],
        duty_type="duty",
    ),
}


# =============================================================================
# CHILDREN ACT 2004
# =============================================================================

CHILDREN_ACT_2004 = {
    "CA2004.s10": LegislativeProvision(
        provision_id="CA2004.s10",
        act="Children Act 2004",
        section="10",
        title="Co-operation to improve well-being",
        text="""Each children's services authority in England must make arrangements to promote co-operation between—
(a) the authority;
(b) each of the authority's relevant partners; and
(c) such other persons or bodies as the authority consider appropriate, being persons or bodies of any 
nature who exercise functions or are engaged in activities in relation to children in the authority's area.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY],
        duty_type="duty",
    ),
    
    "CA2004.s11": LegislativeProvision(
        provision_id="CA2004.s11",
        act="Children Act 2004",
        section="11",
        title="Arrangements to Safeguard and Promote Welfare",
        text="""This section applies to each of the following—
(a) a children's services authority in England;
(b) a district council which is not such an authority;
(c) a Strategic Health Authority;
(d) a Special Health Authority, so far as exercising functions in relation to England, designated by order...
(j) the chief officer of police for a police area in England;
(k) the British Transport Police Force...
Each person and body to which this section applies must make arrangements for ensuring that—
(a) their functions are discharged having regard to the need to safeguard and promote the welfare of children; and
(b) any services provided by another person pursuant to arrangements made by the person or body in the 
discharge of their functions are provided having regard to that need.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY, Agency.POLICE, Agency.CAFCASS],
        duty_type="duty",
        linked_guidance=["Working_Together_2023"],
    ),
}


# =============================================================================
# HUMAN RIGHTS ACT 1998
# =============================================================================

HUMAN_RIGHTS_ACT_1998 = {
    "HRA1998.s6.1": LegislativeProvision(
        provision_id="HRA1998.s6.1",
        act="Human Rights Act 1998",
        section="6",
        subsection="1",
        title="Acts of Public Authorities",
        text="""It is unlawful for a public authority to act in a way which is incompatible with a Convention right.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY, Agency.POLICE, Agency.FAMILY_COURT, Agency.CAFCASS],
        duty_type="prohibition",
    ),
    
    "HRA1998.s6.3": LegislativeProvision(
        provision_id="HRA1998.s6.3",
        act="Human Rights Act 1998",
        section="6",
        subsection="3",
        title="Definition of Public Authority",
        text=""""public authority" includes—
(a) a court or tribunal, and
(b) any person certain of whose functions are functions of a public nature,
but does not include either House of Parliament or a person exercising functions in connection 
with proceedings in Parliament.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY, Agency.POLICE, Agency.FAMILY_COURT, Agency.CAFCASS],
        duty_type="definition",
    ),
    
    "ECHR.Art3": LegislativeProvision(
        provision_id="ECHR.Art3",
        act="European Convention on Human Rights (via HRA 1998)",
        section="Article 3",
        title="Prohibition of Torture",
        text="""No one shall be subjected to torture or to inhuman or degrading treatment or punishment.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY, Agency.POLICE, Agency.FAMILY_COURT],
        duty_type="prohibition",
        linked_cases=["Z_v_UK_2001", "E_v_UK_2002"],
    ),
    
    "ECHR.Art6.1": LegislativeProvision(
        provision_id="ECHR.Art6.1",
        act="European Convention on Human Rights (via HRA 1998)",
        section="Article 6",
        subsection="1",
        title="Right to a Fair Trial",
        text="""In the determination of his civil rights and obligations or of any criminal charge against him, 
everyone is entitled to a fair and public hearing within a reasonable time by an independent and 
impartial tribunal established by law.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.JUDGE, Agency.APPEAL_COURT],
        duty_type="duty",
        linked_cases=["Re_K_2014", "Re_B_S_2013"],
    ),
    
    "ECHR.Art8.1": LegislativeProvision(
        provision_id="ECHR.Art8.1",
        act="European Convention on Human Rights (via HRA 1998)",
        section="Article 8",
        subsection="1",
        title="Right to Respect for Private and Family Life",
        text="""Everyone has the right to respect for his private and family life, his home and his correspondence.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY, Agency.POLICE, Agency.FAMILY_COURT, Agency.CAFCASS, Agency.MEDIA],
        duty_type="duty",
        linked_cases=["Re_B_2013", "Re_B_S_2013", "YC_v_UK_2012", "Kutzner_v_Germany_2002"],
    ),
    
    "ECHR.Art8.2": LegislativeProvision(
        provision_id="ECHR.Art8.2",
        act="European Convention on Human Rights (via HRA 1998)",
        section="Article 8",
        subsection="2",
        title="Article 8 - Justification for Interference",
        text="""There shall be no interference by a public authority with the exercise of this right except such as is 
in accordance with the law and is necessary in a democratic society in the interests of national security, 
public safety or the economic well-being of the country, for the prevention of disorder or crime, 
for the protection of health or morals, or for the protection of the rights and freedoms of others.""",
        duty_bearer=[Agency.LOCAL_AUTHORITY, Agency.POLICE, Agency.FAMILY_COURT],
        duty_type="duty",
        linked_cases=["Re_B_2013", "Re_B_S_2013"],
    ),
    
    "ECHR.Art13": LegislativeProvision(
        provision_id="ECHR.Art13",
        act="European Convention on Human Rights (via HRA 1998)",
        section="Article 13",
        title="Right to an Effective Remedy",
        text="""Everyone whose rights and freedoms as set forth in this Convention are violated shall have 
an effective remedy before a national authority notwithstanding that the violation has been 
committed by persons acting in an official capacity.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.APPEAL_COURT],
        duty_type="duty",
    ),
}


# =============================================================================
# POLICE AND CRIMINAL EVIDENCE ACT 1984 (PACE)
# =============================================================================

PACE_1984 = {
    "PACE.s1": LegislativeProvision(
        provision_id="PACE.s1",
        act="Police and Criminal Evidence Act 1984",
        section="1",
        title="Power to Stop and Search",
        text="""A constable may exercise any power conferred by this section—
(a) in any place to which at the time when he proposes to exercise the power the public or any 
section of the public has access, on payment or otherwise, as of right or by virtue of 
express or implied permission.""",
        duty_bearer=[Agency.POLICE],
        duty_type="power",
    ),
    
    "PACE.s24": LegislativeProvision(
        provision_id="PACE.s24",
        act="Police and Criminal Evidence Act 1984",
        section="24",
        title="Arrest Without Warrant",
        text="""A constable may arrest without a warrant—
(a) anyone who is about to commit an offence;
(b) anyone who is in the act of committing an offence;
(c) anyone whom he has reasonable grounds for suspecting to be about to commit an offence;
(d) anyone whom he has reasonable grounds for suspecting to be committing an offence.""",
        duty_bearer=[Agency.POLICE],
        duty_type="power",
    ),
    
    "PACE.s28.1": LegislativeProvision(
        provision_id="PACE.s28.1",
        act="Police and Criminal Evidence Act 1984",
        section="28",
        subsection="1",
        title="Information to be Given on Arrest",
        text="""Subject to subsection (5) below, where a person is arrested, otherwise than by being informed that 
he is under arrest, the arrest is not lawful unless the person arrested is informed that he is 
under arrest as soon as is practicable after his arrest.""",
        duty_bearer=[Agency.POLICE],
        duty_type="duty",
    ),
    
    "PACE.s56": LegislativeProvision(
        provision_id="PACE.s56",
        act="Police and Criminal Evidence Act 1984",
        section="56",
        title="Right to Have Someone Informed",
        text="""Where a person has been arrested and is being held in custody in a police station or other premises, 
he shall be entitled, if he so requests, to have one friend or relative or other person who is known 
to him or who is likely to take an interest in his welfare told, as soon as is practicable except 
to the extent that delay is permitted by this section, that he has been arrested and is being 
detained there.""",
        duty_bearer=[Agency.POLICE],
        duty_type="duty",
    ),
    
    "PACE.s58.1": LegislativeProvision(
        provision_id="PACE.s58.1",
        act="Police and Criminal Evidence Act 1984",
        section="58",
        subsection="1",
        title="Right to Legal Advice",
        text="""A person arrested and held in custody in a police station or other premises shall be entitled, 
if he so requests, to consult a solicitor privately at any time.""",
        duty_bearer=[Agency.POLICE],
        duty_type="duty",
    ),
    
    "PACE.s76.2": LegislativeProvision(
        provision_id="PACE.s76.2",
        act="Police and Criminal Evidence Act 1984",
        section="76",
        subsection="2",
        title="Confessions - Oppression",
        text="""If, in any proceedings where the prosecution proposes to give in evidence a confession made by an 
accused person, it is represented to the court that the confession was or may have been obtained—
(a) by oppression of the person who made it; or
(b) in consequence of anything said or done which was likely, in the circumstances existing at the time, 
to render unreliable any confession which might be made by him in consequence thereof,
the court shall not allow the confession to be given in evidence against him except in so far as the 
prosecution proves to the court beyond reasonable doubt that the confession (notwithstanding that it 
may be true) was not obtained as aforesaid.""",
        duty_bearer=[Agency.POLICE, Agency.FAMILY_COURT],
        duty_type="prohibition",
    ),
    
    "PACE.s78": LegislativeProvision(
        provision_id="PACE.s78",
        act="Police and Criminal Evidence Act 1984",
        section="78",
        title="Exclusion of Unfair Evidence",
        text="""In any proceedings the court may refuse to allow evidence on which the prosecution proposes to rely 
to be given if it appears to the court that, having regard to all the circumstances, including the 
circumstances in which the evidence was obtained, the admission of the evidence would have such an 
adverse effect on the fairness of the proceedings that the court ought not to admit it.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.POLICE],
        duty_type="power",
    ),
}


# =============================================================================
# DATA PROTECTION ACT 2018 / UK GDPR
# =============================================================================

DATA_PROTECTION_2018 = {
    "DPA2018.s170": LegislativeProvision(
        provision_id="DPA2018.s170",
        act="Data Protection Act 2018",
        section="170",
        title="Unlawful Obtaining of Personal Data",
        text="""It is an offence for a person knowingly or recklessly—
(a) to obtain or disclose personal data without the consent of the controller,
(b) to procure the disclosure of personal data to another person without the consent of the controller, or
(c) after obtaining personal data, to retain it without the consent of the person who was the controller 
in relation to the personal data when it was obtained.""",
        duty_bearer=[Agency.POLICE, Agency.LOCAL_AUTHORITY, Agency.MEDIA],
        duty_type="prohibition",
        penalty="Criminal offence - fine",
    ),
    
    "UKGDPR.Art5": LegislativeProvision(
        provision_id="UKGDPR.Art5",
        act="UK GDPR",
        section="Article 5",
        title="Principles Relating to Processing",
        text="""Personal data shall be:
(a) processed lawfully, fairly and in a transparent manner ('lawfulness, fairness and transparency');
(b) collected for specified, explicit and legitimate purposes ('purpose limitation');
(c) adequate, relevant and limited to what is necessary ('data minimisation');
(d) accurate and, where necessary, kept up to date ('accuracy');
(e) kept in a form which permits identification for no longer than is necessary ('storage limitation');
(f) processed in a manner that ensures appropriate security ('integrity and confidentiality').""",
        duty_bearer=[Agency.POLICE, Agency.LOCAL_AUTHORITY, Agency.CAFCASS, Agency.MEDIA],
        duty_type="duty",
    ),
    
    "UKGDPR.Art6": LegislativeProvision(
        provision_id="UKGDPR.Art6",
        act="UK GDPR",
        section="Article 6",
        title="Lawfulness of Processing",
        text="""Processing shall be lawful only if and to the extent that at least one of the following applies:
(a) the data subject has given consent to the processing;
(b) processing is necessary for the performance of a contract;
(c) processing is necessary for compliance with a legal obligation;
(d) processing is necessary to protect vital interests;
(e) processing is necessary for performance of a task in the public interest;
(f) processing is necessary for legitimate interests.""",
        duty_bearer=[Agency.POLICE, Agency.LOCAL_AUTHORITY, Agency.CAFCASS, Agency.MEDIA],
        duty_type="duty",
    ),
}


# =============================================================================
# CONTEMPT OF COURT ACT 1981 (Media restrictions)
# =============================================================================

CONTEMPT_OF_COURT_1981 = {
    "CCA1981.s2": LegislativeProvision(
        provision_id="CCA1981.s2",
        act="Contempt of Court Act 1981",
        section="2",
        title="Strict Liability Rule",
        text="""The strict liability rule applies only to a publication which creates a substantial risk that the 
course of justice in the proceedings in question will be seriously impeded or prejudiced.""",
        duty_bearer=[Agency.MEDIA],
        duty_type="prohibition",
        penalty="Criminal - imprisonment or fine",
    ),
    
    "CCA1981.s4.2": LegislativeProvision(
        provision_id="CCA1981.s4.2",
        act="Contempt of Court Act 1981",
        section="4",
        subsection="2",
        title="Postponement Orders",
        text="""In any such proceedings the court may, where it appears to be necessary for avoiding a substantial 
risk of prejudice to the administration of justice in those proceedings, or in any other proceedings 
pending or imminent, order that the publication of any report of the proceedings, or any part of the 
proceedings, be postponed for such period as the court thinks necessary for that purpose.""",
        duty_bearer=[Agency.FAMILY_COURT, Agency.MEDIA],
        duty_type="power",
    ),
    
    "AJA1960.s12": LegislativeProvision(
        provision_id="AJA1960.s12",
        act="Administration of Justice Act 1960",
        section="12",
        title="Publication of Family Proceedings",
        text="""The publication of information relating to proceedings before any court sitting in private shall not 
of itself be contempt of court except in the following cases, that is to say—
(a) where the proceedings—
(i) relate to the exercise of the inherent jurisdiction of the High Court with respect to minors;
(ii) are brought under the Children Act 1989 or the Adoption and Children Act 2002; or
(iii) otherwise relate wholly or mainly to the maintenance or upbringing of a minor.""",
        duty_bearer=[Agency.MEDIA, Agency.FAMILY_COURT],
        duty_type="prohibition",
        penalty="Contempt of Court",
    ),
}


# =============================================================================
# EXPORT ALL LEGISLATION
# =============================================================================

ALL_LEGISLATION = {
    **CHILDREN_ACT_1989,
    **CHILDREN_ACT_2004,
    **HUMAN_RIGHTS_ACT_1998,
    **PACE_1984,
    **DATA_PROTECTION_2018,
    **CONTEMPT_OF_COURT_1981,
}


def get_provisions_by_agency(agency: Agency) -> List[LegislativeProvision]:
    """Get all provisions that apply to a specific agency."""
    return [p for p in ALL_LEGISLATION.values() if agency in p.duty_bearer]


def get_provisions_by_act(act_name: str) -> List[LegislativeProvision]:
    """Get all provisions from a specific act."""
    return [p for p in ALL_LEGISLATION.values() if act_name.lower() in p.act.lower()]

