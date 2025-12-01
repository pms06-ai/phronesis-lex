"""
Toulmin Legal Argument Builder

Constructs formal legal arguments using the Toulmin model:
- Claim: The conclusion being argued
- Data/Grounds: The evidence supporting the claim  
- Warrant: The legal principle connecting data to claim
- Backing: Authority supporting the warrant (legislation, case law)
- Qualifier: Strength of the argument
- Rebuttal: Potential counter-arguments and responses
"""

import sqlite3
import json
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class ArgumentStrength(Enum):
    DEFINITIVE = "definitive"      # Conclusive, no reasonable counter
    STRONG = "strong"              # Very compelling, limited counters
    MODERATE = "moderate"          # Good argument, some vulnerabilities
    QUALIFIED = "qualified"        # Arguable, needs careful presentation


@dataclass
class ToulminArgument:
    """A legal argument structured using Toulmin's model."""
    
    claim: str                          # The conclusion
    grounds: List[str]                  # Evidence/facts
    warrant: str                        # Legal principle
    backing: List[str]                  # Statutory/case law authority
    qualifier: ArgumentStrength
    rebuttals: List[Dict[str, str]]    # Counter-arguments and responses
    
    argument_type: str = ""             # e.g., "procedural_failure"
    relevant_agency: str = ""           # e.g., "Police"
    complaint_route: str = ""           # e.g., "IOPC"
    

# Pre-defined legal warrants (the "so what" connecting facts to conclusions)
LEGAL_WARRANTS = {
    'police_investigation': {
        'warrant': 'Police have a duty to conduct objective investigations without prejudice to any outcome (R v Commissioner of Police of the Metropolis, ex parte Blackburn [1968])',
        'backing': [
            'Police and Criminal Evidence Act 1984',
            'College of Policing Authorised Professional Practice',
            'Criminal Procedure and Investigations Act 1996',
        ]
    },
    'disclosure': {
        'warrant': 'The prosecution has a continuing duty to disclose material that might reasonably be considered capable of undermining the prosecution case or assisting the defence (CPIA 1996 s.3)',
        'backing': [
            'Criminal Procedure and Investigations Act 1996',
            'R v H and C [2004] UKHL 3',
            'Attorney General\'s Guidelines on Disclosure',
        ]
    },
    'threshold': {
        'warrant': 'A care order may only be made if the threshold criteria in s.31(2) Children Act 1989 are satisfied: the child is suffering or likely to suffer significant harm attributable to parental care not being what a reasonable parent would give',
        'backing': [
            'Children Act 1989 s.31(2)',
            'Re B (Children) [2008] UKHL 35',
            'Re S-B (Children) [2009] UKSC 17',
        ]
    },
    'proportionality': {
        'warrant': 'Any interference with Article 8 rights must be in accordance with law, pursue a legitimate aim, and be necessary and proportionate (Re B (A Child) [2013] UKSC 33)',
        'backing': [
            'Human Rights Act 1998',
            'ECHR Article 8',
            'Re B (A Child) [2013] UKSC 33',
            'Re B-S (Children) [2013] EWCA Civ 1146',
        ]
    },
    'fair_trial': {
        'warrant': 'Every person is entitled to a fair and public hearing within a reasonable time by an independent and impartial tribunal (ECHR Article 6)',
        'backing': [
            'Human Rights Act 1998',
            'ECHR Article 6',
            'Re K and H [2015] EWCA Civ 543',
        ]
    },
    'cafcass_independence': {
        'warrant': 'CAFCASS officers must maintain independence and form their own professional judgment, not simply adopt the position of any party (CJCS Act 2000 s.12)',
        'backing': [
            'Criminal Justice and Court Services Act 2000 s.12',
            'CAFCASS Operating Framework',
            'Re W (Children) [2009] EWCA Civ 59',
        ]
    },
    'lucas_direction': {
        'warrant': 'A lie told by a party is not necessarily evidence of guilt or wrongdoing - the Lucas direction requires analysis of why someone might lie (R v Lucas [1981] QB 720)',
        'backing': [
            'R v Lucas [1981] QB 720',
            'A County Council v K, D and L [2005] EWHC 144',
        ]
    },
    'welfare_checklist': {
        'warrant': 'When determining any question about a child\'s upbringing, the child\'s welfare is the court\'s paramount consideration, having regard to the welfare checklist (CA 1989 s.1)',
        'backing': [
            'Children Act 1989 s.1(1)',
            'Children Act 1989 s.1(3) welfare checklist',
        ]
    },
    'candour': {
        'warrant': 'Local authorities owe a duty of candour to the court and parties, requiring full and frank disclosure of all relevant information (Re C (A Child) [2019] EWCA Civ 1998)',
        'backing': [
            'Working Together to Safeguard Children 2023',
            'Re C (A Child) [2019] EWCA Civ 1998',
            'FPR 2010 Part 21',
        ]
    }
}


class ArgumentBuilder:
    """Builds Toulmin-structured legal arguments from evidence."""
    
    def __init__(self, db_path: str = 'Phronesis/data/db/phronesis.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
    def build_argument(
        self, 
        argument_type: str,
        agency: str,
        grounds: List[str],
        additional_context: str = ""
    ) -> ToulminArgument:
        """Build a Toulmin argument from evidence."""
        
        # Get warrant and backing
        warrant_data = LEGAL_WARRANTS.get(argument_type, {})
        warrant = warrant_data.get('warrant', 'Legal principle to be researched')
        backing = warrant_data.get('backing', [])
        
        # Generate claim based on argument type and evidence
        claim = self._generate_claim(argument_type, agency, grounds)
        
        # Assess strength
        qualifier = self._assess_strength(grounds, argument_type)
        
        # Generate rebuttals and responses
        rebuttals = self._generate_rebuttals(argument_type, agency)
        
        # Determine complaint route
        complaint_route = self._get_complaint_route(agency)
        
        return ToulminArgument(
            claim=claim,
            grounds=grounds,
            warrant=warrant,
            backing=backing,
            qualifier=qualifier,
            rebuttals=rebuttals,
            argument_type=argument_type,
            relevant_agency=agency,
            complaint_route=complaint_route
        )
    
    def _generate_claim(self, argument_type: str, agency: str, grounds: List[str]) -> str:
        """Generate the claim/conclusion."""
        
        claims = {
            'police_investigation': f"The police investigation was conducted with prejudice and failed to meet required standards",
            'disclosure': f"The prosecution/police failed to comply with disclosure obligations under CPIA 1996",
            'threshold': f"The s.31 threshold criteria were not satisfied on the evidence presented",
            'proportionality': f"The interference with Article 8 rights was disproportionate and not necessary",
            'fair_trial': f"The proceedings violated Article 6 rights to a fair trial",
            'cafcass_independence': f"The CAFCASS officer failed to maintain independence and adopted the Local Authority's position",
            'lucas_direction': f"The court failed to properly apply Lucas direction when assessing credibility",
            'welfare_checklist': f"The court failed to properly consider all elements of the welfare checklist",
            'candour': f"The Local Authority failed in their duty of candour to the court",
        }
        
        base_claim = claims.get(argument_type, f"{agency} failed to meet statutory duties")
        
        # Strengthen based on evidence count
        if len(grounds) >= 5:
            return f"There is substantial evidence that {base_claim.lower()}"
        else:
            return base_claim
    
    def _assess_strength(self, grounds: List[str], argument_type: str) -> ArgumentStrength:
        """Assess the strength of the argument."""
        
        # More evidence = stronger
        if len(grounds) >= 10:
            return ArgumentStrength.STRONG
        elif len(grounds) >= 5:
            return ArgumentStrength.MODERATE
        else:
            return ArgumentStrength.QUALIFIED
    
    def _generate_rebuttals(self, argument_type: str, agency: str) -> List[Dict[str, str]]:
        """Generate likely counter-arguments and responses."""
        
        rebuttals = {
            'police_investigation': [
                {
                    'counter': 'Investigation was complex and required careful consideration',
                    'response': 'Complexity does not excuse failure to follow APP or statutory disclosure requirements'
                },
                {
                    'counter': 'Suspects were released NFA proving fair process',
                    'response': 'NFA after 23 months suggests flawed investigation from outset'
                }
            ],
            'disclosure': [
                {
                    'counter': 'All relevant material was disclosed',
                    'response': 'Evidence shows specific material was disclosed late or not at all'
                },
                {
                    'counter': 'Material was not relevant to proceedings',
                    'response': 'Relevance determination should not be made unilaterally'
                }
            ],
            'threshold': [
                {
                    'counter': 'Children at risk from family circumstances',
                    'response': 'Risk must be evidenced and attributable to parental care, not external circumstances'
                },
                {
                    'counter': 'Protective action necessary',
                    'response': 'Protective measures must be proportionate and threshold must still be met'
                }
            ],
            'proportionality': [
                {
                    'counter': 'Child\'s welfare required intervention',
                    'response': 'Even if welfare requires action, the least interventionist option must be considered'
                },
                {
                    'counter': 'Parents under investigation for serious offences',
                    'response': 'Investigation alone, without charge or conviction, is not evidence of risk'
                }
            ],
            'fair_trial': [
                {
                    'counter': 'All parties had opportunity to be heard',
                    'response': 'Opportunity alone is insufficient if evidence was not fairly considered'
                },
                {
                    'counter': 'Court made findings on available evidence',
                    'response': 'Evidence must be complete and fairly presented for findings to be sound'
                }
            ],
            'cafcass_independence': [
                {
                    'counter': 'Officer formed independent view which happened to align with LA',
                    'response': 'Pattern of alignment without critical analysis suggests lack of independence'
                }
            ],
        }
        
        return rebuttals.get(argument_type, [])
    
    def _get_complaint_route(self, agency: str) -> str:
        """Get the appropriate complaint route."""
        
        routes = {
            'Police': 'IOPC under Police Reform Act 2002',
            'police': 'IOPC under Police Reform Act 2002',
            'Local Authority': 'LGSCO or Judicial Review',
            'local_authority': 'LGSCO or Judicial Review',
            'CAFCASS': 'CAFCASS Complaints then Parliamentary Ombudsman',
            'cafcass': 'CAFCASS Complaints then Parliamentary Ombudsman',
            'Family Court': 'Appeal or JCIO',
            'family_court': 'Appeal or JCIO',
            'Social Worker': 'HCPC Fitness to Practise',
            'social_worker': 'HCPC Fitness to Practise',
            'media': 'Ofcom Broadcasting Code complaint',
            'appeal_court': 'Supreme Court / ECHR',
        }
        return routes.get(agency, 'Seek legal advice')
    
    def build_all_arguments(self) -> List[ToulminArgument]:
        """Build arguments for all identified breaches."""
        
        arguments = []
        
        # Load accountability audit
        if os.path.exists('data/accountability_audit_report.json'):
            with open('data/accountability_audit_report.json', encoding='utf-8') as f:
                audit = json.load(f)
        else:
            return arguments
        
        # Build arguments from audit findings
        agency_results = audit.get('agency_results', {})
        
        for agency, agency_result in agency_results.items():
            for breach in agency_result.get('breaches', []):
                # Determine argument type
                arg_type = self._map_breach_to_argument_type(breach)
                
                # Get grounds (evidence)
                grounds = [f"Evidence of '{breach.get('indicator')}' found in {breach.get('evidence_count')} documents"]
                
                # Build argument
                argument = self.build_argument(
                    argument_type=arg_type,
                    agency=agency,
                    grounds=grounds
                )
                
                arguments.append(argument)
        
        return arguments
    
    def _map_breach_to_argument_type(self, breach: Dict) -> str:
        """Map a breach to an argument type."""
        
        duty = breach.get('duty_title', '').lower()
        
        if 'disclosure' in duty:
            return 'disclosure'
        elif 'threshold' in duty or 'section 31' in duty:
            return 'threshold'
        elif 'article 8' in duty or 'proportional' in duty:
            return 'proportionality'
        elif 'article 6' in duty or 'fair' in duty:
            return 'fair_trial'
        elif 'independence' in duty or 'impartial' in duty:
            return 'cafcass_independence'
        elif 'candour' in duty:
            return 'candour'
        elif 'welfare' in duty:
            return 'welfare_checklist'
        elif 'investig' in duty:
            return 'police_investigation'
        else:
            return 'police_investigation'
    
    def close(self):
        self.conn.close()


def generate_argument_pack():
    """Generate comprehensive argument pack."""
    
    builder = ArgumentBuilder()
    
    print("="*70)
    print("TOULMIN LEGAL ARGUMENT BUILDER")
    print("="*70)
    
    # Build all arguments
    print("\nBuilding legal arguments from evidence...")
    arguments = builder.build_all_arguments()
    print(f"  Generated {len(arguments)} arguments")
    
    # Group by agency
    by_agency = {}
    for arg in arguments:
        agency = arg.relevant_agency
        if agency not in by_agency:
            by_agency[agency] = []
        by_agency[agency].append(arg)
    
    # Generate output
    output = []
    output.append("="*70)
    output.append("LEGAL ARGUMENT PACK")
    output.append("="*70)
    output.append(f"\nCase: PE23C50095 - JFD vs SJS Family Proceedings")
    output.append(f"Generated: {datetime.now().strftime('%d %B %Y %H:%M')}")
    output.append(f"\nTotal arguments: {len(arguments)}")
    
    for agency, agency_args in by_agency.items():
        output.append(f"\n\n{'='*70}")
        output.append(f"{agency.upper()} - {len(agency_args)} ARGUMENTS")
        output.append("="*70)
        output.append(f"\nComplaint Route: {agency_args[0].complaint_route}")
        
        for i, arg in enumerate(agency_args[:5], 1):  # Top 5 per agency
            output.append(f"\n\n--- ARGUMENT {i}: {arg.argument_type.upper()} ---")
            output.append(f"\nCLAIM:")
            output.append(f"  {arg.claim}")
            
            output.append(f"\nGROUNDS (Evidence):")
            for ground in arg.grounds:
                output.append(f"  • {ground}")
            
            output.append(f"\nWARRANT (Legal Principle):")
            output.append(f"  {arg.warrant}")
            
            output.append(f"\nBACKING (Authority):")
            for back in arg.backing:
                output.append(f"  • {back}")
            
            output.append(f"\nSTRENGTH: {arg.qualifier.value.upper()}")
            
            if arg.rebuttals:
                output.append(f"\nPOTENTIAL COUNTER-ARGUMENTS:")
                for reb in arg.rebuttals[:2]:
                    output.append(f"\n  Counter: {reb['counter']}")
                    output.append(f"  Response: {reb['response']}")
    
    # Save
    os.makedirs('data/analysis', exist_ok=True)
    
    with open('data/analysis/LEGAL_ARGUMENTS.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    # Also save as JSON
    json_output = {
        'generated_at': datetime.now().isoformat(),
        'total_arguments': len(arguments),
        'by_agency': {
            agency: [{
                'claim': arg.claim,
                'grounds': arg.grounds,
                'warrant': arg.warrant,
                'backing': arg.backing,
                'qualifier': arg.qualifier.value,
                'rebuttals': arg.rebuttals,
                'argument_type': arg.argument_type,
                'complaint_route': arg.complaint_route
            } for arg in args]
            for agency, args in by_agency.items()
        }
    }
    
    with open('data/analysis/legal_arguments.json', 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2)
    
    print(f"\nArgument pack saved to: data/analysis/LEGAL_ARGUMENTS.txt")
    print(f"JSON data saved to: data/analysis/legal_arguments.json")
    
    # Print summary
    print("\n" + "="*70)
    print("ARGUMENTS BY AGENCY")
    print("="*70)
    
    for agency, args in sorted(by_agency.items(), key=lambda x: -len(x[1])):
        print(f"\n{agency}: {len(args)} arguments")
        print(f"  Complaint route: {args[0].complaint_route}")
        
        # Count by strength
        strengths = {}
        for arg in args:
            s = arg.qualifier.value
            strengths[s] = strengths.get(s, 0) + 1
        
        for s, count in sorted(strengths.items()):
            print(f"  {s}: {count}")
    
    builder.close()


if __name__ == "__main__":
    generate_argument_pack()

