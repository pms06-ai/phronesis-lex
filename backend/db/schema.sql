-- Phronesis LEX Database Schema
-- Forensic Legal Investigation Platform
-- SQLite-compatible schema

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Cases (multi-case support)
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    reference TEXT NOT NULL UNIQUE,
    title TEXT,
    court TEXT,
    case_type TEXT CHECK(case_type IN ('family', 'civil', 'criminal', 'tribunal', 'other')),
    status TEXT CHECK(status IN ('active', 'closed', 'appeal', 'archived')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT  -- JSON string for flexible data
);

-- Professionals (all case participants)
CREATE TABLE IF NOT EXISTS professionals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT,
    profession TEXT CHECK(profession IN (
        'judge', 'barrister', 'solicitor', 'social_worker',
        'psychologist', 'psychiatrist', 'cafcass_officer',
        'guardian', 'expert_witness', 'police_officer', 'other'
    )),
    qualifications TEXT,  -- JSON array
    registration_body TEXT,
    registration_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_professionals_normalized ON professionals(normalized_name);

-- Professional Capacities (who said what, in what role)
CREATE TABLE IF NOT EXISTS professional_capacities (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    professional_id TEXT NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    capacity TEXT CHECK(capacity IN (
        'presiding_judge', 'circuit_judge', 'district_judge', 'magistrate',
        'lead_counsel', 'junior_counsel', 'instructed_solicitor',
        'expert_witness', 'professional_witness', 'lay_witness',
        'children_guardian', 'cafcass_officer', 'social_worker',
        'applicant', 'respondent', 'intervenor', 'other'
    )),
    party_represented TEXT CHECK(party_represented IN (
        'applicant', 'respondent', 'child', 'local_authority',
        'guardian', 'intervenor', 'court', 'none'
    )),
    start_date DATE,
    end_date DATE,
    UNIQUE(case_id, professional_id, capacity)
);

CREATE INDEX IF NOT EXISTS idx_capacities_case ON professional_capacities(case_id);

-- Documents (full text storage)
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    original_path TEXT,
    folder TEXT,
    doc_type TEXT CHECK(doc_type IN (
        'judgment', 'order', 'statement', 'position_statement',
        'report', 'assessment', 'transcript', 'correspondence',
        'disclosure', 'bundle', 'skeleton_argument', 'application',
        'witness_statement', 'expert_report', 'other'
    )),
    author_professional_id TEXT REFERENCES professionals(id),
    date_created DATE,
    date_filed DATE,
    full_text TEXT,
    word_count INTEGER DEFAULT 0,
    page_count INTEGER DEFAULT 0,
    processed_at TIMESTAMP,
    ocr_quality REAL CHECK(ocr_quality >= 0 AND ocr_quality <= 1),
    file_hash TEXT,
    metadata TEXT  -- JSON
);

CREATE INDEX IF NOT EXISTS idx_documents_case ON documents(case_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type);

-- Entity Extractions (NLP-extracted entities)
CREATE TABLE IF NOT EXISTS entity_extractions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    entity_text TEXT NOT NULL,
    normalized_text TEXT,
    confidence REAL CHECK(confidence >= 0 AND confidence <= 1),
    start_offset INTEGER,
    end_offset INTEGER,
    context TEXT,
    metadata TEXT  -- JSON
);

CREATE INDEX IF NOT EXISTS idx_extractions_doc ON entity_extractions(document_id);
CREATE INDEX IF NOT EXISTS idx_extractions_type ON entity_extractions(entity_type);

-- Claims/Arguments (CRITICAL: First-class objects)
CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    document_id TEXT REFERENCES documents(id) ON DELETE SET NULL,
    claim_type TEXT CHECK(claim_type IN (
        'assertion', 'allegation', 'finding', 'conclusion',
        'recommendation', 'opinion', 'observation', 'submission'
    )),
    claim_text TEXT NOT NULL,
    claimant_professional_id TEXT REFERENCES professionals(id),
    claimant_capacity TEXT,
    target_entity TEXT,
    date_made DATE,
    context TEXT,
    page_number INTEGER,
    paragraph_number INTEGER,
    ai_extracted BOOLEAN DEFAULT FALSE,
    ai_confidence REAL,
    -- FCIP Epistemic Fields
    modality TEXT CHECK(modality IN ('asserted', 'reported', 'alleged', 'denied', 'hypothetical')),
    polarity TEXT CHECK(polarity IN ('affirm', 'negate')) DEFAULT 'affirm',
    certainty REAL CHECK(certainty >= 0 AND certainty <= 1),
    certainty_markers TEXT,  -- JSON array
    asserted_by TEXT,
    time_expression TEXT,
    extraction_prompt_hash TEXT,
    extractor_model TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_claims_case ON claims(case_id);
CREATE INDEX IF NOT EXISTS idx_claims_document ON claims(document_id);
CREATE INDEX IF NOT EXISTS idx_claims_claimant ON claims(claimant_professional_id);

-- Evidence Links (what supports each claim)
CREATE TABLE IF NOT EXISTS evidence_links (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    evidence_type TEXT CHECK(evidence_type IN (
        'document', 'testimony', 'expert_opinion', 'physical',
        'contemporaneous_record', 'third_party', 'admission', 'other'
    )),
    evidence_document_id TEXT REFERENCES documents(id),
    evidence_description TEXT,
    evidence_strength TEXT CHECK(evidence_strength IN ('strong', 'moderate', 'weak', 'absent', 'contradictory')),
    is_cited BOOLEAN DEFAULT FALSE,
    is_available BOOLEAN DEFAULT TRUE,
    ai_assessment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidence_claim ON evidence_links(claim_id);

-- Competing Claims (claim vs counter-claim)
CREATE TABLE IF NOT EXISTS competing_claims (
    id TEXT PRIMARY KEY,
    claim_a_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    claim_b_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    relationship TEXT CHECK(relationship IN (
        'contradicts', 'supports', 'qualifies', 'supersedes',
        'partially_contradicts', 'contextualizes'
    )),
    resolution TEXT CHECK(resolution IN (
        'a_accepted', 'b_accepted', 'both_rejected', 'unresolved',
        'ignored', 'compromise', 'pending'
    )),
    resolved_by_professional_id TEXT REFERENCES professionals(id),
    resolution_document_id TEXT REFERENCES documents(id),
    resolution_reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK(claim_a_id != claim_b_id)
);

CREATE INDEX IF NOT EXISTS idx_competing_a ON competing_claims(claim_a_id);
CREATE INDEX IF NOT EXISTS idx_competing_b ON competing_claims(claim_b_id);

-- Timeline Events (temporal reconstruction)
CREATE TABLE IF NOT EXISTS timeline_events (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    event_time TIME,
    event_end_date DATE,
    event_type TEXT CHECK(event_type IN (
        'incident', 'allegation', 'report', 'assessment',
        'hearing', 'decision', 'order', 'filing',
        'disclosure', 'meeting', 'contact', 'other'
    )),
    description TEXT NOT NULL,
    source_document_id TEXT REFERENCES documents(id),
    participants TEXT,  -- JSON array of professional IDs
    location TEXT,
    significance TEXT CHECK(significance IN ('critical', 'important', 'routine', 'minor')),
    verified BOOLEAN DEFAULT FALSE,
    metadata TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_timeline_case ON timeline_events(case_id);
CREATE INDEX IF NOT EXISTS idx_timeline_date ON timeline_events(event_date);

-- Decision Points (what was known when decisions made)
CREATE TABLE IF NOT EXISTS decision_points (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    timeline_event_id TEXT REFERENCES timeline_events(id),
    decision_maker_id TEXT REFERENCES professionals(id),
    decision_text TEXT NOT NULL,
    decision_type TEXT CHECK(decision_type IN (
        'interim_order', 'final_order', 'direction', 'ruling',
        'recommendation', 'assessment_conclusion', 'finding', 'other'
    )),
    available_evidence TEXT,  -- JSON array of document IDs
    unavailable_evidence TEXT,  -- JSON array - evidence that came later
    alternatives_considered TEXT,  -- JSON array
    reasoning_given TEXT,
    ai_assessment TEXT,
    ai_reasonableness_score REAL CHECK(ai_reasonableness_score >= 0 AND ai_reasonableness_score <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_decisions_case ON decision_points(case_id);

-- Bias Indicators (detected cognitive biases)
CREATE TABLE IF NOT EXISTS bias_indicators (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    document_id TEXT REFERENCES documents(id),
    professional_id TEXT REFERENCES professionals(id),
    bias_type TEXT CHECK(bias_type IN (
        'confirmation', 'outcome', 'anchoring', 'availability',
        'hindsight', 'attribution', 'groupthink', 'authority',
        'narrative', 'selective_attention', 'other'
    )),
    evidence_text TEXT NOT NULL,
    context TEXT,
    severity TEXT CHECK(severity IN ('high', 'medium', 'low')),
    ai_confidence REAL CHECK(ai_confidence >= 0 AND ai_confidence <= 1),
    ai_reasoning TEXT,
    -- FCIP statistical fields
    z_score REAL,
    p_value REAL,
    baseline_mean REAL,
    baseline_std REAL,
    baseline_id TEXT,
    direction TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bias_case ON bias_indicators(case_id);
CREATE INDEX IF NOT EXISTS idx_bias_professional ON bias_indicators(professional_id);


-- Contradictions (FCIP Revolutionary Feature)
-- Cross-document contradiction detection
CREATE TABLE IF NOT EXISTS contradictions (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    
    -- The conflicting claims
    claim_a_id TEXT REFERENCES claims(id) ON DELETE CASCADE,
    claim_b_id TEXT REFERENCES claims(id) ON DELETE CASCADE,
    
    -- Contradiction classification
    contradiction_type TEXT CHECK(contradiction_type IN (
        'direct',           -- Opposite assertions about same thing
        'self',             -- Same author contradicts themselves (CRITICAL)
        'temporal',         -- Timeline impossibility
        'modality',         -- Allegation treated as fact
        'value',            -- Different values for same attribute
        'attribution',      -- Disputes about who said/did what
        'quotation',        -- Misrepresented quotes
        'omission'          -- Material context omitted
    )),
    
    -- Severity and confidence
    severity TEXT CHECK(severity IN ('critical', 'high', 'medium', 'low', 'info')),
    confidence REAL CHECK(confidence >= 0 AND confidence <= 1),
    semantic_similarity REAL CHECK(semantic_similarity >= 0 AND semantic_similarity <= 1),
    
    -- Analysis
    description TEXT,
    conflicting_elements TEXT,  -- JSON array
    
    -- Attribution (for self-contradictions)
    author_a TEXT,
    author_b TEXT,
    is_self_contradiction BOOLEAN DEFAULT FALSE,
    
    -- Temporal context
    date_a TEXT,
    date_b TEXT,
    temporal_gap_days INTEGER,
    
    -- Legal significance
    legal_significance TEXT,
    relevant_case_law TEXT,  -- JSON array
    recommended_action TEXT,
    
    -- Metadata
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detection_model TEXT,
    reviewed BOOLEAN DEFAULT FALSE,
    reviewer_notes TEXT,
    
    CHECK(claim_a_id != claim_b_id)
);

CREATE INDEX IF NOT EXISTS idx_contradictions_case ON contradictions(case_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_type ON contradictions(contradiction_type);
CREATE INDEX IF NOT EXISTS idx_contradictions_severity ON contradictions(severity);
CREATE INDEX IF NOT EXISTS idx_contradictions_self ON contradictions(is_self_contradiction);

-- Legal References (legislation, case law, standards)
CREATE TABLE IF NOT EXISTS legal_references (
    id TEXT PRIMARY KEY,
    reference_type TEXT CHECK(reference_type IN (
        'primary_legislation', 'secondary_legislation',
        'case_law', 'practice_direction', 'protocol',
        'professional_guideline', 'standard', 'other'
    )),
    citation TEXT NOT NULL UNIQUE,
    full_title TEXT,
    source_url TEXT,
    relevant_text TEXT,
    category TEXT,
    applies_to TEXT,  -- JSON array of case types
    effective_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_legal_citation ON legal_references(citation);

-- Procedural Requirements (what should have happened)
CREATE TABLE IF NOT EXISTS procedural_requirements (
    id TEXT PRIMARY KEY,
    legal_reference_id TEXT NOT NULL REFERENCES legal_references(id) ON DELETE CASCADE,
    requirement_text TEXT NOT NULL,
    applies_to_professional TEXT,  -- JSON array
    timing_requirement TEXT,
    mandatory BOOLEAN DEFAULT TRUE,
    evidence_of_compliance TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compliance Checks (did they follow procedure?)
CREATE TABLE IF NOT EXISTS compliance_checks (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    procedural_requirement_id TEXT NOT NULL REFERENCES procedural_requirements(id),
    professional_id TEXT REFERENCES professionals(id),
    compliant BOOLEAN,
    evidence_document_id TEXT REFERENCES documents(id),
    non_compliance_description TEXT,
    impact_assessment TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_compliance_case ON compliance_checks(case_id);

-- Analysis Runs (track AI analysis sessions)
CREATE TABLE IF NOT EXISTS analysis_runs (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    run_type TEXT CHECK(run_type IN ('full', 'incremental', 'targeted', 'document', 'bias', 'claims')),
    status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed', 'cancelled')) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    documents_analyzed INTEGER DEFAULT 0,
    claims_extracted INTEGER DEFAULT 0,
    biases_detected INTEGER DEFAULT 0,
    model_used TEXT,
    prompt_version TEXT,
    total_tokens INTEGER DEFAULT 0,
    cost_estimate REAL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_runs_case ON analysis_runs(case_id);

-- Contradictions (detected inconsistencies between claims)
CREATE TABLE IF NOT EXISTS contradictions (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    claim_a_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    claim_b_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    contradiction_type TEXT CHECK(contradiction_type IN (
        'direct', 'temporal', 'self_contradiction', 'modality_shift',
        'value', 'attribution', 'quotation', 'omission'
    )),
    severity TEXT CHECK(severity IN ('critical', 'high', 'medium', 'low', 'info')) DEFAULT 'medium',
    claim_a_text TEXT,
    claim_b_text TEXT,
    claim_a_source TEXT,
    claim_b_source TEXT,
    claim_a_author TEXT,
    claim_b_author TEXT,
    same_author BOOLEAN DEFAULT FALSE,
    semantic_similarity REAL CHECK(semantic_similarity >= 0 AND semantic_similarity <= 1),
    confidence REAL CHECK(confidence >= 0 AND confidence <= 1),
    explanation TEXT,
    legal_significance TEXT,
    recommended_action TEXT,
    case_law_reference TEXT,
    detection_method TEXT,
    reviewed BOOLEAN DEFAULT FALSE,
    reviewer_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(claim_a_id, claim_b_id)
);

CREATE INDEX IF NOT EXISTS idx_contradictions_case ON contradictions(case_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_type ON contradictions(contradiction_type);
CREATE INDEX IF NOT EXISTS idx_contradictions_severity ON contradictions(severity);


-- FCIP v5 enhancements to claims table (additional columns)
-- Note: Run as ALTER TABLE if table already exists

-- Toulmin Arguments (structured legal reasoning)
CREATE TABLE IF NOT EXISTS arguments (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    claim_text TEXT NOT NULL,
    grounds TEXT,  -- JSON array
    warrant TEXT,
    warrant_rule_id TEXT,
    backing TEXT,  -- JSON array
    qualifier TEXT,
    rebuttal TEXT,  -- JSON array
    falsifiability_conditions TEXT,  -- JSON array
    missing_evidence TEXT,  -- JSON array
    alternative_explanations TEXT,  -- JSON array
    confidence_lower REAL CHECK(confidence_lower >= 0 AND confidence_lower <= 1),
    confidence_upper REAL CHECK(confidence_upper >= 0 AND confidence_upper <= 1),
    confidence_mean REAL CHECK(confidence_mean >= 0 AND confidence_mean <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_arguments_case ON arguments(case_id);


-- Deadline Alerts (from temporal parsing)
CREATE TABLE IF NOT EXISTS deadline_alerts (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    document_id TEXT REFERENCES documents(id),
    raw_expression TEXT,
    deadline_date DATE,
    deadline_type TEXT CHECK(deadline_type IN (
        'absolute', 'relative', 'working_days', 'immediate', 'before_hearing'
    )),
    anchor_event TEXT,
    offset_value INTEGER,
    offset_unit TEXT,
    confidence REAL CHECK(confidence >= 0 AND confidence <= 1),
    is_working_days BOOLEAN DEFAULT FALSE,
    status TEXT CHECK(status IN ('pending', 'acknowledged', 'completed', 'missed')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deadlines_case ON deadline_alerts(case_id);
CREATE INDEX IF NOT EXISTS idx_deadlines_date ON deadline_alerts(deadline_date);


-- Legal Rules Library
CREATE TABLE IF NOT EXISTS legal_rules (
    rule_id TEXT PRIMARY KEY,
    short_name TEXT NOT NULL,
    full_citation TEXT NOT NULL,
    text TEXT,
    category TEXT CHECK(category IN ('welfare', 'threshold', 'evidence', 'professional', 'procedural')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Bias Baselines (for statistical comparison)
CREATE TABLE IF NOT EXISTS bias_baselines (
    baseline_id TEXT PRIMARY KEY,
    doc_type TEXT NOT NULL,
    metric TEXT NOT NULL,
    mean REAL NOT NULL,
    std_dev REAL NOT NULL,
    corpus_size INTEGER DEFAULT 100,
    source TEXT CHECK(source IN ('empirical', 'estimated', 'calibrated')) DEFAULT 'estimated',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(doc_type, metric)
);


-- Entity Aliases (learned during analysis)
CREATE TABLE IF NOT EXISTS entity_aliases (
    id TEXT PRIMARY KEY,
    professional_id TEXT NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    alias_text TEXT NOT NULL,
    confidence REAL CHECK(confidence >= 0 AND confidence <= 1),
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(professional_id, alias_text)
);

CREATE INDEX IF NOT EXISTS idx_aliases_professional ON entity_aliases(professional_id);


-- Triggers for updated_at
CREATE TRIGGER IF NOT EXISTS update_cases_timestamp
    AFTER UPDATE ON cases
    BEGIN
        UPDATE cases SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
