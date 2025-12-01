"""
Management command to seed the legal rules database.
Contains UK Family Court legal rules, case law, and practice directions.
"""
from django.core.management.base import BaseCommand
from django_backend.analysis.models import LegalRule, BiasBaseline


LEGAL_RULES = [
    # Children Act 1989
    {
        'rule_id': 'CA1989.s1.1',
        'short_name': 'Paramountcy Principle',
        'full_citation': 'Children Act 1989, Section 1(1)',
        'text': (
            "When a court determines any question with respect to the upbringing of a child, "
            "the child's welfare shall be the court's paramount consideration."
        ),
        'category': 'welfare',
        'keywords': ['paramountcy', 'welfare', 'child', 'upbringing'],
    },
    {
        'rule_id': 'CA1989.s1.2',
        'short_name': 'No Delay Principle',
        'full_citation': 'Children Act 1989, Section 1(2)',
        'text': (
            "In any proceedings in which any question with respect to the upbringing of a child arises, "
            "the court shall have regard to the general principle that any delay in determining the "
            "question is likely to prejudice the welfare of the child."
        ),
        'category': 'procedural',
        'keywords': ['delay', 'prejudice', 'welfare', 'proceedings'],
    },
    {
        'rule_id': 'CA1989.s1.3',
        'short_name': 'Welfare Checklist',
        'full_citation': 'Children Act 1989, Section 1(3)',
        'text': (
            "A court shall have regard in particular to: "
            "(a) the ascertainable wishes and feelings of the child concerned (considered in light of age and understanding); "
            "(b) physical, emotional and educational needs; "
            "(c) likely effect of any change in circumstances; "
            "(d) age, sex, background and any characteristics which the court considers relevant; "
            "(e) any harm suffered or at risk of suffering; "
            "(f) capability of each parent and any other relevant person; "
            "(g) range of powers available to the court."
        ),
        'category': 'welfare',
        'keywords': ['welfare', 'checklist', 'wishes', 'feelings', 'harm', 'needs'],
    },
    {
        'rule_id': 'CA1989.s31.2',
        'short_name': 'Threshold Criteria',
        'full_citation': 'Children Act 1989, Section 31(2)',
        'text': (
            "A court may only make a care order or supervision order if it is satisfied: "
            "(a) that the child is suffering, or is likely to suffer, significant harm; and "
            "(b) that the harm, or likelihood of harm, is attributable to: "
            "(i) the care given to the child, or likely to be given if the order were not made, "
            "not being what it would be reasonable to expect a parent to give; or "
            "(ii) the child being beyond parental control."
        ),
        'category': 'threshold',
        'keywords': ['threshold', 'significant harm', 'care order', 'supervision'],
    },
    
    # Practice Directions
    {
        'rule_id': 'PD12J',
        'short_name': 'Domestic Abuse PD',
        'full_citation': 'Practice Direction 12J FPR 2010',
        'text': (
            "The court must at all stages of the proceedings consider whether domestic abuse is raised "
            "as an issue; and if so, must identify at the earliest opportunity the factual and welfare "
            "issues involved and consider the nature of any allegation. Where allegations are made, "
            "the court must consider the impact of the abuse on the child and the parent with whom "
            "the child is living."
        ),
        'category': 'welfare',
        'keywords': ['domestic abuse', 'allegations', 'fact-finding', 'child arrangements'],
    },
    {
        'rule_id': 'PD12B',
        'short_name': 'Child Arrangements Programme',
        'full_citation': 'Practice Direction 12B FPR 2010',
        'text': (
            "The Child Arrangements Programme applies to all private law proceedings under the "
            "Children Act 1989 and sets out the approach to be taken by the court at all stages."
        ),
        'category': 'procedural',
        'keywords': ['CAP', 'private law', 'arrangements', 'procedure'],
    },
    {
        'rule_id': 'PD25C',
        'short_name': 'Expert Evidence',
        'full_citation': 'Practice Direction 25C FPR 2010',
        'text': (
            "Expert evidence should be restricted to that which is reasonably required to resolve "
            "the proceedings. The court's permission is required before any expert can be instructed. "
            "Experts must be objective and independent."
        ),
        'category': 'evidence',
        'keywords': ['expert', 'evidence', 'permission', 'independent'],
    },
    
    # Key Case Law
    {
        'rule_id': 'Re_B_2008',
        'short_name': 'Re B Standard of Proof',
        'full_citation': 'Re B (Children) [2008] UKHL 35',
        'text': (
            "The standard of proof in care proceedings is the balance of probabilities. "
            "There is no room for a finding that threshold is crossed on the basis that there is "
            "a 'real possibility' that the child was harmed. If a fact is to be used as the basis "
            "for a finding, it must be proved. Unproved allegations must be left out of account entirely."
        ),
        'category': 'evidence',
        'keywords': ['standard of proof', 'balance of probabilities', 'threshold', 'unproved'],
    },
    {
        'rule_id': 'Re_W_Lucas',
        'short_name': 'Lucas Direction',
        'full_citation': 'R v Lucas [1981] QB 720; Re H-C (Children) [2016] EWCA Civ 136',
        'text': (
            "A person may lie for many reasons. The fact that a person has lied about one matter "
            "does not mean they have lied about everything. A lie is only probative of guilt if it "
            "is told to conceal the truth about the matter in issue and not for some other reason. "
            "The court must consider: (1) whether there was a lie; (2) was there a good reason for "
            "the lie; (3) was the lie relevant to the issue."
        ),
        'category': 'evidence',
        'keywords': ['lucas', 'lies', 'credibility', 'probative'],
    },
    {
        'rule_id': 'Re_A_2015',
        'short_name': 'Holistic Evidence Assessment',
        'full_citation': 'Re A (A Child) [2015] EWFC 11',
        'text': (
            "Evidence cannot be evaluated in separate compartments. The court must take account of "
            "all the evidence and consider each piece of evidence in the context of all the other evidence. "
            "The roles of the court and expert are entirely distinct. The court must reach its own "
            "conclusion on the evidence."
        ),
        'category': 'evidence',
        'keywords': ['holistic', 'evidence', 'compartments', 'context'],
    },
    {
        'rule_id': 'Re_C_Hearsay',
        'short_name': 'Hearsay Evidence',
        'full_citation': 'Re C and B (Children) (Care Proceedings: Guidelines) [1998] 1 FLR 1',
        'text': (
            "Hearsay evidence is admissible in family proceedings. However, the weight to be given "
            "to such evidence depends on its nature and source. The court must assess the reliability "
            "of the hearsay and consider whether the original maker could be called."
        ),
        'category': 'evidence',
        'keywords': ['hearsay', 'weight', 'reliability', 'admissible'],
    },
    {
        'rule_id': 'Re_J_Burden',
        'short_name': 'Burden of Proof',
        'full_citation': 'Re J (Children) [2013] UKSC 9',
        'text': (
            "The burden of proving a fact remains throughout on the party who asserts it. "
            "There is no obligation on a party against whom an allegation is made to prove "
            "a negative or provide an alternative explanation."
        ),
        'category': 'evidence',
        'keywords': ['burden', 'proof', 'assertion', 'negative'],
    },
    
    # Professional Standards
    {
        'rule_id': 'FJC_Guidance',
        'short_name': 'Expert Witness Guidance',
        'full_citation': 'Family Justice Council Guidelines for Expert Witnesses',
        'text': (
            "Experts must be objective and independent. They must distinguish clearly between fact "
            "and opinion. They must acknowledge the limitations of their expertise and methodology. "
            "They must not act as advocates for either party."
        ),
        'category': 'professional',
        'keywords': ['expert', 'objective', 'independent', 'opinion'],
    },
    {
        'rule_id': 'SRA_Code',
        'short_name': 'SRA Code of Conduct',
        'full_citation': 'SRA Standards and Regulations',
        'text': (
            "Solicitors must act in the best interests of each client. They must act with honesty "
            "and integrity. They must not mislead or attempt to mislead the court. "
            "They must maintain trust and acting fairly."
        ),
        'category': 'professional',
        'keywords': ['solicitor', 'honesty', 'integrity', 'mislead'],
    },
    {
        'rule_id': 'BSB_Handbook',
        'short_name': 'BSB Handbook',
        'full_citation': 'Bar Standards Board Handbook',
        'text': (
            "Barristers must not knowingly or recklessly mislead the court. They owe a duty to the "
            "court to ensure the proper administration of justice. The duty to the court overrides "
            "any obligations to clients."
        ),
        'category': 'professional',
        'keywords': ['barrister', 'duty', 'court', 'mislead'],
    },
    {
        'rule_id': 'SWCCF',
        'short_name': 'Social Work Capabilities Framework',
        'full_citation': 'Professional Capabilities Framework for Social Work',
        'text': (
            "Social workers must exercise professional judgement. They must be evidence-informed "
            "and distinguish between fact and opinion. They must acknowledge uncertainty and "
            "the limitations of their assessments."
        ),
        'category': 'professional',
        'keywords': ['social worker', 'judgement', 'evidence', 'uncertainty'],
    },
    {
        'rule_id': 'CAFCASS_Standards',
        'short_name': 'CAFCASS Operating Framework',
        'full_citation': 'CAFCASS Operating Framework and Practice Standards',
        'text': (
            "CAFCASS practitioners must be objective and fair to all parties. They must ascertain "
            "and represent the wishes and feelings of children. They must distinguish between "
            "allegations and findings. Their reports must be balanced and evidence-based."
        ),
        'category': 'professional',
        'keywords': ['cafcass', 'guardian', 'wishes', 'balanced'],
    },
]


BIAS_BASELINES = [
    # Section 7 Reports
    {'baseline_id': 'section_7_report_certainty', 'doc_type': 'section_7_report', 'metric': 'certainty_ratio', 'mean': 0.40, 'std_dev': 0.15},
    {'baseline_id': 'section_7_report_negative', 'doc_type': 'section_7_report', 'metric': 'negative_ratio', 'mean': 0.45, 'std_dev': 0.12},
    {'baseline_id': 'section_7_report_extreme', 'doc_type': 'section_7_report', 'metric': 'extreme_ratio', 'mean': 0.25, 'std_dev': 0.10},
    
    # Section 37 Reports
    {'baseline_id': 'section_37_report_certainty', 'doc_type': 'section_37_report', 'metric': 'certainty_ratio', 'mean': 0.42, 'std_dev': 0.14},
    {'baseline_id': 'section_37_report_negative', 'doc_type': 'section_37_report', 'metric': 'negative_ratio', 'mean': 0.50, 'std_dev': 0.13},
    {'baseline_id': 'section_37_report_extreme', 'doc_type': 'section_37_report', 'metric': 'extreme_ratio', 'mean': 0.28, 'std_dev': 0.11},
    
    # Psychological Reports
    {'baseline_id': 'psychological_report_certainty', 'doc_type': 'psychological_report', 'metric': 'certainty_ratio', 'mean': 0.35, 'std_dev': 0.12},
    {'baseline_id': 'psychological_report_negative', 'doc_type': 'psychological_report', 'metric': 'negative_ratio', 'mean': 0.48, 'std_dev': 0.14},
    {'baseline_id': 'psychological_report_extreme', 'doc_type': 'psychological_report', 'metric': 'extreme_ratio', 'mean': 0.20, 'std_dev': 0.08},
    
    # Social Work Reports
    {'baseline_id': 'social_work_report_certainty', 'doc_type': 'social_work_report', 'metric': 'certainty_ratio', 'mean': 0.42, 'std_dev': 0.15},
    {'baseline_id': 'social_work_report_negative', 'doc_type': 'social_work_report', 'metric': 'negative_ratio', 'mean': 0.52, 'std_dev': 0.14},
    {'baseline_id': 'social_work_report_extreme', 'doc_type': 'social_work_report', 'metric': 'extreme_ratio', 'mean': 0.30, 'std_dev': 0.12},
    
    # CAFCASS Analysis
    {'baseline_id': 'cafcass_analysis_certainty', 'doc_type': 'cafcass_analysis', 'metric': 'certainty_ratio', 'mean': 0.38, 'std_dev': 0.13},
    {'baseline_id': 'cafcass_analysis_negative', 'doc_type': 'cafcass_analysis', 'metric': 'negative_ratio', 'mean': 0.45, 'std_dev': 0.12},
    {'baseline_id': 'cafcass_analysis_extreme', 'doc_type': 'cafcass_analysis', 'metric': 'extreme_ratio', 'mean': 0.22, 'std_dev': 0.09},
    
    # Witness Statements
    {'baseline_id': 'witness_statement_certainty', 'doc_type': 'witness_statement', 'metric': 'certainty_ratio', 'mean': 0.55, 'std_dev': 0.18},
    {'baseline_id': 'witness_statement_negative', 'doc_type': 'witness_statement', 'metric': 'negative_ratio', 'mean': 0.50, 'std_dev': 0.20},
    {'baseline_id': 'witness_statement_extreme', 'doc_type': 'witness_statement', 'metric': 'extreme_ratio', 'mean': 0.35, 'std_dev': 0.15},
    
    # Expert Reports
    {'baseline_id': 'expert_report_certainty', 'doc_type': 'expert_report', 'metric': 'certainty_ratio', 'mean': 0.32, 'std_dev': 0.10},
    {'baseline_id': 'expert_report_negative', 'doc_type': 'expert_report', 'metric': 'negative_ratio', 'mean': 0.42, 'std_dev': 0.12},
    {'baseline_id': 'expert_report_extreme', 'doc_type': 'expert_report', 'metric': 'extreme_ratio', 'mean': 0.18, 'std_dev': 0.07},
]


class Command(BaseCommand):
    help = 'Seed the database with UK Family Court legal rules and bias baselines'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing rules',
        )
    
    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write(self.style.NOTICE('Seeding legal rules...'))
        
        rules_created = 0
        rules_updated = 0
        
        for rule_data in LEGAL_RULES:
            rule, created = LegalRule.objects.update_or_create(
                rule_id=rule_data['rule_id'],
                defaults={
                    'short_name': rule_data['short_name'],
                    'full_citation': rule_data['full_citation'],
                    'text': rule_data['text'],
                    'category': rule_data['category'],
                    'keywords': rule_data.get('keywords', []),
                }
            )
            if created:
                rules_created += 1
                self.stdout.write(f"  Created: {rule.short_name}")
            else:
                rules_updated += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Legal rules: {rules_created} created, {rules_updated} updated'
            )
        )
        
        self.stdout.write(self.style.NOTICE('Seeding bias baselines...'))
        
        baselines_created = 0
        baselines_updated = 0
        
        for baseline_data in BIAS_BASELINES:
            baseline, created = BiasBaseline.objects.update_or_create(
                baseline_id=baseline_data['baseline_id'],
                defaults={
                    'doc_type': baseline_data['doc_type'],
                    'metric': baseline_data['metric'],
                    'mean': baseline_data['mean'],
                    'std_dev': baseline_data['std_dev'],
                    'source': 'estimated',
                    'corpus_size': 100,
                }
            )
            if created:
                baselines_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Bias baselines: {baselines_created} created, {baselines_updated} updated'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS('\nSeeding complete!')
        )

