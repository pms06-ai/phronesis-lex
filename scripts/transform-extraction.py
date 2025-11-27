#!/usr/bin/env python3
"""
Transform entity_extraction_results.json into real-case-data.js for Phronesis LEX
"""
import json
import re
from collections import defaultdict
from pathlib import Path

# Source and destination
SOURCE = Path("/mnt/c/Users/pstep/TKSA_v6/tksa-monorepo/TKSA/entity_extraction_results.json")
DEST = Path("/mnt/c/Users/pstep/phronesis-lex/js/data/real-case-data.js")

def normalize_entity_name(text, entity_type):
    """Clean and normalize entity text"""
    # Remove excess whitespace
    text = ' '.join(text.split())

    # Skip if too long (likely extraction error)
    if len(text) > 80:
        return None

    # Skip if too short
    if len(text) < 3:
        return None

    # Type-specific normalization
    if entity_type == 'UK_JUDGE':
        # Extract judge name patterns
        match = re.search(r'(HHJ|DJ|Judge|His Honour Judge|Her Honour Judge)\s+([A-Z][a-zA-Z\-]+)', text, re.IGNORECASE)
        if match:
            return f"{match.group(1)} {match.group(2)}".title()
        return None

    if entity_type == 'UK_LOCAL_AUTHORITY':
        # Look for known patterns
        match = re.search(r'(Cambridge|Suffolk|Norfolk|Essex)[a-z]*\s*(County\s*Council|CC)', text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}shire County Council"
        return None

    if entity_type == 'UK_POLICE_FORCE':
        match = re.search(r'(Cambridge|Suffolk|Norfolk|Essex)[a-z]*\s*(Constabulary|Police)', text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}shire Constabulary"
        if 'Chief Constable' in text:
            match = re.search(r'Chief Constable of ([A-Za-z]+)', text)
            if match:
                return f"Chief Constable of {match.group(1)}shire Constabulary"
        return None

    if entity_type == 'UK_COURT':
        if 'Family Court' in text:
            match = re.search(r'(Cambridge|Ipswich|Suffolk|Norwich)\s*Family\s*Court', text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} Family Court"
            if 'Family Court' in text and len(text) < 30:
                return text.strip()
        return None

    if entity_type == 'CASE_NUMBER':
        # Match case number patterns
        match = re.search(r'PE\d{2}[CP]\d{5}', text)
        if match:
            return match.group(0)
        return None

    if entity_type == 'SOLICITOR_FIRM':
        # Skip noise
        if any(x in text.lower() for x in ['whatsapp', 'google', 'search', 'contact']):
            return None
        if len(text) < 30:
            return text.strip()
        return None

    if entity_type == 'DATE':
        # Keep dates as-is if reasonably formatted
        if len(text) < 30:
            return text.strip()
        return None

    return text.strip() if len(text) < 50 else None


def main():
    print("Loading extraction data...")
    with open(SOURCE, 'r') as f:
        raw_data = json.load(f)

    print(f"Processing {len(raw_data)} documents...")

    # Collect all extractions
    all_extractions = []
    documents = []
    entity_index = defaultdict(lambda: {'occurrences': 0, 'documents': set(), 'confidences': []})

    for doc in raw_data:
        doc_id = doc['document_id']
        doc_name = doc['filename']
        doc_folder = doc['folder']

        doc_entity_count = 0
        doc_entities = []

        for idx, entity in enumerate(doc.get('entities', [])):
            raw_text = entity['entity_text']
            entity_type = entity['entity_type']
            confidence = entity.get('confidence', 0.85)
            context = entity.get('context', '')

            # Normalize the entity name
            normalized = normalize_entity_name(raw_text, entity_type)
            if not normalized:
                continue

            # Create extraction record
            extraction = {
                'id': f"ext-{len(all_extractions)}",
                'entityType': entity_type,
                'rawText': raw_text,
                'normalizedText': normalized,
                'confidence': confidence,
                'documentId': doc_id,
                'documentName': doc_name,
                'folder': doc_folder,
                'context': context[:200] if context else ''
            }
            all_extractions.append(extraction)
            doc_entity_count += 1
            doc_entities.append(normalized)

            # Update entity index
            key = f"{entity_type}::{normalized}"
            entity_index[key]['type'] = entity_type
            entity_index[key]['name'] = normalized
            entity_index[key]['occurrences'] += 1
            entity_index[key]['documents'].add(doc_id)
            entity_index[key]['confidences'].append(confidence)

        # Add document record
        documents.append({
            'id': doc_id,
            'name': doc_name,
            'folder': doc_folder,
            'entityCount': doc_entity_count,
            'entities': list(set(doc_entities))
        })

    print(f"Filtered to {len(all_extractions)} valid extractions")

    # Build unique entities list
    unique_entities = []
    for idx, (key, data) in enumerate(sorted(entity_index.items(), key=lambda x: -x[1]['occurrences'])):
        unique_entities.append({
            'id': f"ent-{idx}",
            'name': data['name'],
            'type': data['type'],
            'occurrences': data['occurrences'],
            'documents': list(data['documents']),
            'avgConfidence': round(sum(data['confidences']) / len(data['confidences']), 2)
        })

    print(f"Found {len(unique_entities)} unique entities")

    # Generate co-occurrence relationships
    print("Generating co-occurrence relationships...")
    relationships = defaultdict(lambda: {'documents': set(), 'strength': 0})

    # Create entity name to ID mapping
    name_to_id = {e['name']: e['id'] for e in unique_entities}

    for doc in documents:
        entities_in_doc = doc['entities']
        # Create pairs
        for i in range(len(entities_in_doc)):
            for j in range(i + 1, len(entities_in_doc)):
                e1, e2 = entities_in_doc[i], entities_in_doc[j]
                if e1 == e2:
                    continue
                # Sort to ensure consistent key
                pair = tuple(sorted([e1, e2]))
                relationships[pair]['documents'].add(doc['id'])
                relationships[pair]['strength'] += 1

    # Convert to list, filter weak relationships
    relationship_list = []
    for (e1, e2), data in relationships.items():
        if data['strength'] < 2:  # Skip single co-occurrences
            continue
        if e1 not in name_to_id or e2 not in name_to_id:
            continue
        relationship_list.append({
            'from': name_to_id[e1],
            'to': name_to_id[e2],
            'fromName': e1,
            'toName': e2,
            'type': 'co-occurrence',
            'documents': list(data['documents']),
            'strength': data['strength'],
            'label': None
        })

    # Sort by strength
    relationship_list.sort(key=lambda x: -x['strength'])
    print(f"Generated {len(relationship_list)} relationships (strength >= 2)")

    # Manual relationship overrides for key entities
    manual_relationships = [
        {'from': 'HHJ Gordon-Saker', 'to': 'Cambridge Family Court', 'label': 'presides at', 'type': 'professional'},
        {'from': 'Cambridgeshire County Council', 'to': 'Cambridge Family Court', 'label': 'applicant to', 'type': 'legal'},
        {'from': 'Suffolk County Council', 'to': 'Ipswich Family Court', 'label': 'applicant to', 'type': 'legal'},
        {'from': 'Cambridgeshire Constabulary', 'to': 'Cambridgeshire County Council', 'label': 'discloses to', 'type': 'administrative'},
    ]

    # Apply manual overrides
    for manual in manual_relationships:
        for rel in relationship_list:
            if rel['fromName'] == manual['from'] and rel['toName'] == manual['to']:
                rel['label'] = manual['label']
                rel['type'] = manual['type']
            elif rel['toName'] == manual['from'] and rel['fromName'] == manual['to']:
                rel['label'] = manual['label']
                rel['type'] = manual['type']

    # Build final data structure
    output = {
        'case': {
            'id': 'PE23C50095',
            'reference': 'PE23C50095',
            'title': 'Cambridgeshire CC v Stephen',
            'court': 'Cambridge Family Court',
            'judge': 'HHJ Gordon-Saker',
            'status': 'active',
            'createdAt': '2023-06-09'
        },
        'entityExtractions': all_extractions,
        'uniqueEntities': unique_entities,
        'documents': documents,
        'relationships': relationship_list[:100],  # Top 100 strongest relationships
        'stats': {
            'totalExtractions': len(all_extractions),
            'uniqueEntities': len(unique_entities),
            'documents': len(documents),
            'relationships': len(relationship_list),
            'byType': {}
        }
    }

    # Count by type
    for e in unique_entities:
        t = e['type']
        output['stats']['byType'][t] = output['stats']['byType'].get(t, 0) + 1

    # Write JavaScript file
    print(f"Writing to {DEST}...")
    js_content = f"""// Real Case Data - Transformed from entity_extraction_results.json
// Generated automatically - do not edit manually
// Case: PE23C50095 - Cambridgeshire CC v Stephen

const realCaseData = {json.dumps(output, indent=2)};

// Export for use in stores
if (typeof window !== 'undefined') {{
    window.realCaseData = realCaseData;
}}
"""

    DEST.parent.mkdir(parents=True, exist_ok=True)
    with open(DEST, 'w') as f:
        f.write(js_content)

    print("Done!")
    print(f"\nSummary:")
    print(f"  Extractions: {output['stats']['totalExtractions']}")
    print(f"  Unique entities: {output['stats']['uniqueEntities']}")
    print(f"  Documents: {output['stats']['documents']}")
    print(f"  Relationships: {len(output['relationships'])}")
    print(f"  By type: {output['stats']['byType']}")


if __name__ == '__main__':
    main()
