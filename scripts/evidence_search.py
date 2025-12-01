"""
Evidence Search Engine

Powerful search across all claims and documents to find specific evidence.
Supports keyword, phrase, person, and topic searches.
"""

import sqlite3
import json
import re
import os
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Optional

DB_PATH = 'Phronesis/data/db/phronesis.db'


class EvidenceSearchEngine:
    """Search engine for finding evidence across the case."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
    def search(self, query: str, search_type: str = 'keyword', limit: int = 50) -> Dict:
        """
        Main search method.
        
        search_type options:
            - keyword: Simple keyword search
            - phrase: Exact phrase search  
            - person: Search for mentions of a person
            - topic: Search by topic category
            - date: Search by date range
        """
        
        if search_type == 'keyword':
            return self.keyword_search(query, limit)
        elif search_type == 'phrase':
            return self.phrase_search(query, limit)
        elif search_type == 'person':
            return self.person_search(query, limit)
        elif search_type == 'topic':
            return self.topic_search(query, limit)
        else:
            return self.keyword_search(query, limit)
    
    def keyword_search(self, keywords: str, limit: int = 50) -> Dict:
        """Search for claims containing any of the keywords."""
        
        terms = keywords.lower().split()
        conditions = ' OR '.join([f"LOWER(claim_text) LIKE '%{t}%'" for t in terms])
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT c.*, d.filename, d.title, d.document_category
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE {conditions}
            LIMIT ?
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            'query': keywords,
            'type': 'keyword',
            'count': len(results),
            'results': results
        }
    
    def phrase_search(self, phrase: str, limit: int = 50) -> Dict:
        """Search for exact phrase matches."""
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.*, d.filename, d.title, d.document_category
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE LOWER(claim_text) LIKE ?
            LIMIT ?
        """, (f'%{phrase.lower()}%', limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            'query': phrase,
            'type': 'phrase',
            'count': len(results),
            'results': results
        }
    
    def person_search(self, person_name: str, limit: int = 50) -> Dict:
        """Search for all mentions of a person."""
        
        # Handle name variations
        name_lower = person_name.lower()
        
        # Common variations
        variations = [name_lower]
        
        # Add common variations
        if 'samantha' in name_lower:
            variations.extend(['samantha', 'sam', 'mrs stephen', 'mother'])
        if 'paul' in name_lower and 'stephen' in name_lower:
            variations.extend(['paul', 'mr stephen', 'step-father', 'stepfather'])
        if 'joshua' in name_lower or 'dunmore' in name_lower:
            variations.extend(['joshua', 'dunmore', 'josh', 'father', 'deceased father'])
        if 'ryan' in name_lower:
            variations.extend(['ryan', 'child', 'children', 'boy'])
        if 'alderton' in name_lower:
            variations.extend(['alderton', 'grandfather', 'maternal grandfather', 'stephen alderton'])
        if 'dounias' in name_lower:
            variations.extend(['dounias', 'dci', 'sio', 'investigating officer'])
        if 'atkinson' in name_lower:
            variations.extend(['atkinson', 'dc', 'officer'])
        
        conditions = ' OR '.join([f"LOWER(claim_text) LIKE '%{v}%'" for v in variations])
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT c.*, d.filename, d.title, d.document_category
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE {conditions}
            LIMIT ?
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        
        # Also check asserted_by
        cursor.execute("""
            SELECT c.*, d.filename, d.title, d.document_category
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE LOWER(asserted_by) LIKE ?
            LIMIT ?
        """, (f'%{name_lower}%', limit))
        
        author_results = [dict(row) for row in cursor.fetchall()]
        
        return {
            'query': person_name,
            'type': 'person',
            'mentioned_count': len(results),
            'authored_count': len(author_results),
            'mentioned_in': results[:25],
            'authored': author_results[:25]
        }
    
    def topic_search(self, topic: str, limit: int = 50) -> Dict:
        """Search by predefined topic."""
        
        topic_keywords = {
            'murder': ['murder', 'killed', 'shooting', 'death', 'deceased', 'homicide'],
            'conspiracy': ['conspiracy', 'conspired', 'plotted', 'planned', 'premeditated'],
            'arrest': ['arrested', 'detained', 'custody', 'bail', 'interview under caution'],
            'threshold': ['threshold', 'significant harm', 'section 31', 's.31', 'likely to suffer'],
            'contact': ['contact', 'visits', 'family time', 'supervised contact', 'direct contact'],
            'care': ['care order', 'interim care', 'ICO', 'care proceedings', 'foster'],
            'cafcass': ['cafcass', 'guardian', 'section 7', 's.7 report', 'welfare report'],
            'police': ['police', 'officer', 'constabulary', 'investigation', 'disclosure'],
            'credibility': ['credibility', 'credible', 'believe', 'truth', 'honest', 'lied', 'false'],
            'welfare': ['welfare', 'best interests', 'ascertainable wishes', 'needs'],
            'emotional': ['emotional', 'distress', 'anxiety', 'trauma', 'psychological'],
            'disclosure': ['disclosed', 'disclosure', 'provided', 'evidence', 'material'],
            'hearing': ['hearing', 'court', 'judge', 'directions', 'final hearing'],
            'appeal': ['appeal', 'appealed', 'grounds', 'permission'],
        }
        
        topic_lower = topic.lower()
        keywords = topic_keywords.get(topic_lower, [topic_lower])
        
        conditions = ' OR '.join([f"LOWER(claim_text) LIKE '%{k}%'" for k in keywords])
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT c.*, d.filename, d.title, d.document_category
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE {conditions}
            ORDER BY c.created_at DESC
            LIMIT ?
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            'query': topic,
            'type': 'topic',
            'keywords_used': keywords,
            'count': len(results),
            'results': results
        }
    
    def find_contradictions_for(self, claim_text: str, limit: int = 20) -> Dict:
        """Find claims that might contradict a given claim."""
        
        # Extract key terms
        words = claim_text.lower().split()
        significant_words = [w for w in words if len(w) > 4 and w not in 
                           ['about', 'would', 'could', 'should', 'their', 'there', 'where', 'which', 'being']][:5]
        
        if not significant_words:
            return {'query': claim_text, 'potential_contradictions': []}
        
        # Search for similar claims
        conditions = ' OR '.join([f"LOWER(claim_text) LIKE '%{w}%'" for w in significant_words])
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT c.*, d.filename, d.title, d.document_category
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE ({conditions})
            AND claim_text != ?
            LIMIT ?
        """, (claim_text, limit * 2))
        
        candidates = [dict(row) for row in cursor.fetchall()]
        
        # Filter for potential contradictions (opposite polarity indicators)
        contradiction_pairs = [
            ('did', 'did not'), ('was', 'was not'), ('has', 'has not'),
            ('is', 'is not'), ('agreed', 'refused'), ('true', 'false'),
            ('yes', 'no'), ('always', 'never')
        ]
        
        potential_contradictions = []
        claim_lower = claim_text.lower()
        
        for candidate in candidates:
            cand_text = (candidate.get('claim_text') or '').lower()
            
            for pos, neg in contradiction_pairs:
                if (pos in claim_lower and neg in cand_text) or \
                   (neg in claim_lower and pos in cand_text):
                    potential_contradictions.append(candidate)
                    break
        
        return {
            'query': claim_text[:100] + '...',
            'count': len(potential_contradictions),
            'potential_contradictions': potential_contradictions[:limit]
        }
    
    def get_evidence_for_breach(self, breach_type: str, limit: int = 30) -> Dict:
        """Get evidence supporting a specific breach allegation."""
        
        breach_keywords = {
            'disclosure': ['not disclosed', 'late disclosure', 'failed to provide', 'withheld'],
            'threshold': ['no evidence of harm', 'threshold not met', 'insufficient evidence'],
            'investigation': ['failed to investigate', 'didn\'t follow up', 'ignored', 'dismissed'],
            'candour': ['didn\'t inform', 'failed to tell', 'not told', 'wasn\'t informed'],
            'proportionality': ['disproportionate', 'excessive', 'not necessary', 'extreme'],
            'impartiality': ['one-sided', 'adopted position', 'not independent', 'biased'],
            'fair_trial': ['not heard', 'refused to consider', 'denied opportunity', 'unfair'],
            'accuracy': ['inaccurate', 'wrong', 'incorrect', 'not what I said', 'misquoted'],
        }
        
        keywords = breach_keywords.get(breach_type.lower(), [breach_type.lower()])
        conditions = ' OR '.join([f"LOWER(claim_text) LIKE '%{k}%'" for k in keywords])
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT c.claim_text, c.asserted_by, d.filename, d.document_category
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE {conditions}
            LIMIT ?
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            'breach_type': breach_type,
            'keywords_used': keywords,
            'evidence_count': len(results),
            'evidence': results
        }
    
    def close(self):
        self.conn.close()


def interactive_search():
    """Interactive search mode."""
    
    engine = EvidenceSearchEngine()
    
    print("="*70)
    print("EVIDENCE SEARCH ENGINE")
    print("="*70)
    print("\nSearch types:")
    print("  1. keyword <terms>    - Search for keywords")
    print("  2. phrase <text>      - Search for exact phrase")
    print("  3. person <name>      - Search for person mentions")
    print("  4. topic <topic>      - Search by topic")
    print("  5. breach <type>      - Find evidence for breach")
    print("  6. quit               - Exit")
    print("\nTopics: murder, conspiracy, arrest, threshold, contact, care,")
    print("        cafcass, police, credibility, welfare, disclosure, hearing")
    print("\nBreach types: disclosure, threshold, investigation, candour,")
    print("              proportionality, impartiality, fair_trial, accuracy")
    
    while True:
        print("\n" + "-"*70)
        query = input("\nSearch > ").strip()
        
        if not query:
            continue
        
        if query.lower() == 'quit':
            break
        
        parts = query.split(' ', 1)
        search_type = parts[0].lower()
        search_term = parts[1] if len(parts) > 1 else ''
        
        if search_type == 'keyword':
            results = engine.keyword_search(search_term)
        elif search_type == 'phrase':
            results = engine.phrase_search(search_term)
        elif search_type == 'person':
            results = engine.person_search(search_term)
        elif search_type == 'topic':
            results = engine.topic_search(search_term)
        elif search_type == 'breach':
            results = engine.get_evidence_for_breach(search_term)
        else:
            # Default to keyword search
            results = engine.keyword_search(query)
        
        # Display results
        print(f"\n{'='*70}")
        print(f"RESULTS: {results.get('count', results.get('evidence_count', 0))} found")
        print("="*70)
        
        items = results.get('results', results.get('evidence', results.get('mentioned_in', [])))
        
        for i, item in enumerate(items[:15], 1):
            text = item.get('claim_text', '')[:150]
            doc = item.get('filename', item.get('title', 'Unknown'))
            author = item.get('asserted_by', 'Unknown')
            
            print(f"\n{i}. [{doc}]")
            if author:
                print(f"   Author: {author}")
            print(f"   \"{text}...\"")
    
    engine.close()
    print("\nSearch session ended.")


def run_preset_searches():
    """Run preset searches and save results."""
    
    engine = EvidenceSearchEngine()
    
    print("="*70)
    print("RUNNING PRESET EVIDENCE SEARCHES")
    print("="*70)
    
    preset_searches = [
        ('topic', 'murder', 'Evidence related to murders'),
        ('topic', 'conspiracy', 'Conspiracy allegations'),
        ('topic', 'threshold', 'Threshold arguments'),
        ('breach', 'disclosure', 'Disclosure failures'),
        ('breach', 'fair_trial', 'Fair trial violations'),
        ('person', 'DCI Dounias', 'DCI Dounias mentions'),
        ('person', 'Stephen Alderton', 'Stephen Alderton mentions'),
        ('phrase', 'no further action', 'NFA references'),
        ('phrase', 'insufficient evidence', 'Insufficient evidence'),
    ]
    
    all_results = {}
    
    for search_type, term, description in preset_searches:
        print(f"\n  Searching: {description}...")
        
        if search_type == 'topic':
            results = engine.topic_search(term)
        elif search_type == 'breach':
            results = engine.get_evidence_for_breach(term)
        elif search_type == 'person':
            results = engine.person_search(term)
        elif search_type == 'phrase':
            results = engine.phrase_search(term)
        else:
            results = engine.keyword_search(term)
        
        count = results.get('count', results.get('evidence_count', results.get('mentioned_count', 0)))
        print(f"    Found: {count} results")
        
        all_results[f"{search_type}_{term}"] = {
            'description': description,
            **results
        }
    
    # Save results
    os.makedirs('data/analysis', exist_ok=True)
    with open('data/analysis/preset_search_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: data/analysis/preset_search_results.json")
    
    engine.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_search()
    else:
        run_preset_searches()

