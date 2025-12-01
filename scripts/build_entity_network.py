"""
Entity Relationship Network Builder

Maps all connections between people, agencies, and events in the case.
Generates data for network visualization.
"""

import sqlite3
import json
import os
from collections import defaultdict
from datetime import datetime

DB_PATH = 'Phronesis/data/db/phronesis.db'

# Entity definitions with relationships
ENTITIES = {
    # Family Members (Victim side)
    'Joshua Dunmore': {
        'type': 'victim',
        'role': 'Father',
        'status': 'deceased',
        'relations': ['Gary Dunmore', 'Ryan', 'Freya', 'Samantha Stephen'],
        'events': ['murder_2023-03-29']
    },
    'Gary Dunmore': {
        'type': 'victim',
        'role': 'Grandfather (Paternal)',
        'status': 'deceased',
        'relations': ['Joshua Dunmore', 'Ryan', 'Freya'],
        'events': ['murder_2023-03-29']
    },
    
    # Family Members (Stephen side)
    'Samantha Stephen': {
        'type': 'party',
        'role': 'Mother',
        'status': 'respondent',
        'relations': ['Paul Stephen', 'Ryan', 'Freya', 'Stephen Alderton', 'Joshua Dunmore'],
        'events': ['arrest_2023-03-30', 'arrest_2023-06-07', 'nfa_2025-02-12', 'care_proceedings']
    },
    'Paul Stephen': {
        'type': 'party',
        'role': 'Step-Father',
        'status': 'respondent',
        'relations': ['Samantha Stephen', 'Ryan', 'Freya'],
        'events': ['arrest_2023-03-30', 'arrest_2023-06-07', 'nfa_2025-02-12', 'care_proceedings']
    },
    'Stephen Alderton': {
        'type': 'perpetrator',
        'role': 'Grandfather (Maternal)',
        'status': 'convicted',
        'relations': ['Samantha Stephen', 'Ryan', 'Freya'],
        'events': ['murder_2023-03-29', 'sentenced_2024']
    },
    
    # Children
    'Ryan': {
        'type': 'child',
        'role': 'Child (subject of proceedings)',
        'status': 'subject',
        'relations': ['Joshua Dunmore', 'Samantha Stephen', 'Paul Stephen', 'Freya', 'Mandy Seamark'],
        'events': ['care_proceedings']
    },
    'Freya': {
        'type': 'child',
        'role': 'Child (subject of proceedings)',
        'status': 'subject',
        'relations': ['Joshua Dunmore', 'Samantha Stephen', 'Paul Stephen', 'Ryan', 'Mandy Seamark'],
        'events': ['care_proceedings']
    },
    
    # Other Family
    'Mandy Seamark': {
        'type': 'party',
        'role': 'Paternal Grandmother',
        'status': 'applicant',
        'relations': ['Joshua Dunmore', 'Ryan', 'Freya'],
        'events': ['care_proceedings', 'PE23P30344']
    },
    
    # Police
    'DCI Katie Dounias': {
        'type': 'police',
        'role': 'Senior Investigating Officer',
        'organization': 'BCH Major Crime Unit',
        'relations': ['DC Atkinson', 'Samantha Stephen', 'Paul Stephen'],
        'events': ['murder_investigation', 'arrest_2023-03-30', 'arrest_2023-06-07']
    },
    'DC Atkinson': {
        'type': 'police',
        'role': 'Officer in Case',
        'organization': 'Cambridgeshire Constabulary',
        'relations': ['DCI Katie Dounias', 'Family Court'],
        'events': ['murder_investigation', 'disclosure']
    },
    
    # Social Workers
    'Paul Duggan': {
        'type': 'social_worker',
        'role': 'Allocated Social Worker',
        'organization': 'Cambridgeshire CC',
        'relations': ['Lucy Ardern', 'Local Authority', 'Ryan', 'Freya'],
        'events': ['care_proceedings']
    },
    'Lucy Ardern': {
        'type': 'social_worker',
        'role': 'Social Worker',
        'organization': 'Cambridgeshire CC',
        'relations': ['Paul Duggan', 'Local Authority'],
        'events': ['care_proceedings']
    },
    
    # CAFCASS
    'Guardian': {
        'type': 'cafcass',
        'role': 'Children\'s Guardian',
        'organization': 'CAFCASS',
        'relations': ['Ryan', 'Freya', 'Family Court'],
        'events': ['care_proceedings', 'section_7_reports']
    },
    
    # Court
    'HHJ Gordon-Saker': {
        'type': 'judge',
        'role': 'Circuit Judge',
        'organization': 'Family Court Peterborough',
        'relations': ['Family Court'],
        'events': ['care_proceedings', 'hearings']
    },
    
    # Agencies
    'Local Authority': {
        'type': 'agency',
        'role': 'Applicant in Care Proceedings',
        'organization': 'Cambridgeshire County Council',
        'relations': ['Paul Duggan', 'Lucy Ardern', 'Family Court', 'CAFCASS'],
        'events': ['care_proceedings', 'PE23C50095']
    },
    'CAFCASS': {
        'type': 'agency',
        'role': 'Court Advisor',
        'organization': 'CAFCASS East',
        'relations': ['Guardian', 'Family Court', 'Local Authority'],
        'events': ['section_7_reports', 'care_proceedings']
    },
    'Cambridgeshire Police': {
        'type': 'agency',
        'role': 'Investigating Force',
        'organization': 'Cambridgeshire Constabulary',
        'relations': ['DCI Katie Dounias', 'DC Atkinson'],
        'events': ['murder_investigation']
    },
    'Channel 4': {
        'type': 'media',
        'role': 'Broadcaster',
        'organization': 'Channel 4',
        'relations': [],
        'events': ['24_hours_in_custody']
    }
}

# Key events
EVENTS = {
    'murder_2023-03-29': {
        'date': '2023-03-29',
        'type': 'crime',
        'description': 'Murders of Joshua and Gary Dunmore',
        'severity': 'critical'
    },
    'arrest_2023-03-30': {
        'date': '2023-03-30',
        'type': 'arrest',
        'description': 'Paul & Samantha arrested for conspiracy',
        'severity': 'high'
    },
    'nfa_2023-03-31': {
        'date': '2023-03-31',
        'type': 'police',
        'description': 'Released NFA',
        'severity': 'medium'
    },
    'arrest_2023-06-07': {
        'date': '2023-06-07',
        'type': 'arrest',
        'description': 'Re-arrested',
        'severity': 'high'
    },
    'nfa_2025-02-12': {
        'date': '2025-02-12',
        'type': 'police',
        'description': 'Final NFA - insufficient evidence',
        'severity': 'high'
    },
    'care_proceedings': {
        'date': '2023-06-09',
        'type': 'court',
        'description': 'PE23C50095 - Care Proceedings',
        'severity': 'critical'
    },
    'murder_investigation': {
        'date': '2023-03-29',
        'type': 'investigation',
        'description': 'Operation Scan',
        'severity': 'critical'
    },
    'sentenced_2024': {
        'date': '2024',
        'type': 'court',
        'description': 'Stephen Alderton sentenced to life',
        'severity': 'critical'
    }
}


def build_network():
    """Build network graph data structure."""
    
    nodes = []
    links = []
    
    # Create nodes
    for name, data in ENTITIES.items():
        node = {
            'id': name,
            'label': name,
            'type': data['type'],
            'role': data['role'],
            'organization': data.get('organization', ''),
            'status': data.get('status', ''),
            'group': get_group(data['type'])
        }
        nodes.append(node)
    
    # Create links from relations
    seen_links = set()
    for name, data in ENTITIES.items():
        for relation in data.get('relations', []):
            if relation in ENTITIES:
                link_id = tuple(sorted([name, relation]))
                if link_id not in seen_links:
                    links.append({
                        'source': name,
                        'target': relation,
                        'type': 'relation'
                    })
                    seen_links.add(link_id)
    
    return {'nodes': nodes, 'links': links, 'events': EVENTS}


def get_group(entity_type):
    """Map entity type to color group."""
    groups = {
        'victim': 1,
        'party': 2,
        'child': 3,
        'perpetrator': 4,
        'police': 5,
        'social_worker': 6,
        'cafcass': 7,
        'judge': 8,
        'agency': 9,
        'media': 10
    }
    return groups.get(entity_type, 0)


def analyze_co_occurrences():
    """Analyze which entities appear together in documents."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all claims
    cursor.execute("SELECT claim_text FROM claims")
    claims = [row[0] for row in cursor.fetchall() if row[0]]
    
    conn.close()
    
    # Count co-occurrences
    co_occurrences = defaultdict(int)
    entity_names = list(ENTITIES.keys())
    
    for claim in claims:
        claim_lower = claim.lower()
        found = []
        for name in entity_names:
            if name.lower() in claim_lower:
                found.append(name)
        
        # Create pairs
        for i, name1 in enumerate(found):
            for name2 in found[i+1:]:
                pair = tuple(sorted([name1, name2]))
                co_occurrences[pair] += 1
    
    return dict(co_occurrences)


def build_comprehensive_network():
    """Build comprehensive network with claim analysis."""
    
    print("Building entity relationship network...")
    
    # Basic network
    network = build_network()
    
    # Add co-occurrence data
    print("  Analyzing document co-occurrences...")
    co_occurrences = analyze_co_occurrences()
    
    # Enhance links with strength
    for link in network['links']:
        pair = tuple(sorted([link['source'], link['target']]))
        link['strength'] = co_occurrences.get(pair, 1)
    
    # Add additional links from co-occurrences
    existing_pairs = set(tuple(sorted([l['source'], l['target']])) for l in network['links'])
    
    for pair, count in co_occurrences.items():
        if pair not in existing_pairs and count >= 5:  # Threshold
            network['links'].append({
                'source': pair[0],
                'target': pair[1],
                'type': 'co_occurrence',
                'strength': count
            })
    
    # Summary
    print(f"  Nodes: {len(network['nodes'])}")
    print(f"  Links: {len(network['links'])}")
    print(f"  Co-occurrences analyzed: {len(co_occurrences)}")
    
    return network


def generate_relationship_report():
    """Generate human-readable relationship report."""
    
    report = []
    report.append("="*70)
    report.append("ENTITY RELATIONSHIP REPORT")
    report.append("="*70)
    report.append(f"\nGenerated: {datetime.now().strftime('%d %B %Y %H:%M')}")
    
    # Group by type
    by_type = defaultdict(list)
    for name, data in ENTITIES.items():
        by_type[data['type']].append((name, data))
    
    for entity_type, entities in by_type.items():
        report.append(f"\n\n{entity_type.upper().replace('_', ' ')}")
        report.append("-" * 40)
        
        for name, data in entities:
            report.append(f"\n  {name}")
            report.append(f"    Role: {data['role']}")
            if data.get('organization'):
                report.append(f"    Organization: {data['organization']}")
            if data.get('status'):
                report.append(f"    Status: {data['status']}")
            if data.get('relations'):
                report.append(f"    Relationships: {', '.join(data['relations'][:5])}")
    
    # Key relationships summary
    report.append("\n\n" + "="*70)
    report.append("KEY RELATIONSHIPS")
    report.append("="*70)
    
    relationships = [
        ("Stephen Alderton", "Samantha Stephen", "Father → Daughter"),
        ("Samantha Stephen", "Joshua Dunmore", "Co-Parents (never married)"),
        ("Ryan/Freya", "Joshua Dunmore", "Children → Father"),
        ("Ryan/Freya", "Stephen Alderton", "Grandchildren → Convicted Grandfather"),
        ("Local Authority", "Family Court", "Applicant → Court"),
        ("CAFCASS", "Family Court", "Advisor → Court"),
        ("DCI Dounias", "Murder Investigation", "SIO → Investigation"),
    ]
    
    for entity1, entity2, relationship in relationships:
        report.append(f"\n  {entity1} ←→ {entity2}")
        report.append(f"    {relationship}")
    
    return "\n".join(report)


def main():
    print("="*70)
    print("ENTITY RELATIONSHIP NETWORK BUILDER")
    print("="*70)
    
    # Build network
    network = build_comprehensive_network()
    
    # Save network data
    os.makedirs('data/analysis', exist_ok=True)
    
    with open('data/analysis/entity_network.json', 'w', encoding='utf-8') as f:
        json.dump(network, f, indent=2)
    print(f"\nNetwork data saved to: data/analysis/entity_network.json")
    
    # Generate report
    report = generate_relationship_report()
    
    with open('data/analysis/ENTITY_RELATIONSHIPS.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Relationship report saved to: data/analysis/ENTITY_RELATIONSHIPS.txt")
    
    # Print summary
    print("\n" + "="*70)
    print("NETWORK SUMMARY")
    print("="*70)
    print(f"\nTotal entities: {len(network['nodes'])}")
    print(f"Total relationships: {len(network['links'])}")
    
    print("\nEntities by type:")
    by_type = defaultdict(int)
    for node in network['nodes']:
        by_type[node['type']] += 1
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")
    
    print("\nStrongest relationships (by document co-occurrence):")
    strong_links = sorted(
        [l for l in network['links'] if l.get('strength', 0) > 10],
        key=lambda x: x.get('strength', 0),
        reverse=True
    )[:10]
    
    for link in strong_links:
        print(f"  {link['source']} ↔ {link['target']}: {link.get('strength', 0)} mentions")


if __name__ == "__main__":
    main()

