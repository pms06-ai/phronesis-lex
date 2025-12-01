-- Phronesis LEX Database Schema for Supabase (PostgreSQL)
-- Run this in Supabase SQL Editor: Dashboard > SQL Editor > New Query

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cases
CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference TEXT NOT NULL UNIQUE,
    title TEXT,
    court TEXT,
    case_type TEXT CHECK(case_type IN ('family', 'civil', 'criminal', 'tribunal', 'other')),
    status TEXT CHECK(status IN ('active', 'closed', 'appeal', 'archived')) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Professionals
CREATE TABLE IF NOT EXISTS professionals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    normalized_name TEXT,
    profession TEXT CHECK(profession IN (
        'judge', 'barrister', 'solicitor', 'social_worker',
        'psychologist', 'psychiatrist', 'cafcass_officer',
        'guardian', 'expert_witness', 'police_officer', 'other'
    )),
    qualifications JSONB,
    registration_body TEXT,
    registration_number TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_professionals_normalized ON professionals(normalized_name);

-- Documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    original_path TEXT,
    folder TEXT,
    doc_type TEXT CHECK(doc_type IN (
        'judgment', 'order', 'statement', 'position_statement',
        'report', 'assessment', 'transcript', 'correspondence',
        'disclosure', 'bundle', 'skeleton_argument', 'application',
        'witness_statement', 'expert_report', 'other'
    )),
    author_professional_id UUID REFERENCES professionals(id),
    date_created DATE,
    date_filed DATE,
    full_text TEXT,
    word_count INTEGER DEFAULT 0,
    page_count INTEGER DEFAULT 0,
    processed_at TIMESTAMPTZ,
    ocr_quality REAL CHECK(ocr_quality >= 0 AND ocr_quality <= 1),
    file_hash TEXT,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_documents_case ON documents(case_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type);

-- Claims
CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    claim_type TEXT CHECK(claim_type IN (
        'assertion', 'allegation', 'finding', 'conclusion',
        'recommendation', 'opinion', 'observation', 'submission'
    )),
    claim_text TEXT NOT NULL,
    claimant_professional_id UUID REFERENCES professionals(id),
    claimant_capacity TEXT,
    target_entity TEXT,
    date_made DATE,
    context TEXT,
    page_number INTEGER,
    paragraph_number INTEGER,
    ai_extracted BOOLEAN DEFAULT FALSE,
    ai_confidence REAL,
    modality TEXT CHECK(modality IN ('asserted', 'reported', 'alleged', 'denied', 'hypothetical')),
    polarity TEXT CHECK(polarity IN ('affirm', 'negate')) DEFAULT 'affirm',
    certainty REAL CHECK(certainty >= 0 AND certainty <= 1),
    certainty_markers JSONB,
    asserted_by TEXT,
    time_expression TEXT,
    extraction_prompt_hash TEXT,
    extractor_model TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_claims_case ON claims(case_id);
CREATE INDEX IF NOT EXISTS idx_claims_document ON claims(document_id);

-- Timeline Events
CREATE TABLE IF NOT EXISTS timeline_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    event_time TIME,
    event_end_date DATE,
    event_type TEXT CHECK(event_type IN (
        'incident', 'allegation', 'report', 'assessment',
        'hearing', 'decision', 'order', 'filing',
        'disclosure', 'meeting', 'contact', 'other'
    )),
    description TEXT NOT NULL,
    source_document_id UUID REFERENCES documents(id),
    participants JSONB,
    location TEXT,
    significance TEXT CHECK(significance IN ('critical', 'important', 'routine', 'minor')),
    verified BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_timeline_case ON timeline_events(case_id);
CREATE INDEX IF NOT EXISTS idx_timeline_date ON timeline_events(event_date);

-- Contradictions
CREATE TABLE IF NOT EXISTS contradictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    claim_a_id UUID REFERENCES claims(id) ON DELETE CASCADE,
    claim_b_id UUID REFERENCES claims(id) ON DELETE CASCADE,
    contradiction_type TEXT CHECK(contradiction_type IN (
        'direct', 'self', 'temporal', 'modality', 'value', 'attribution', 'quotation', 'omission'
    )),
    severity TEXT CHECK(severity IN ('critical', 'high', 'medium', 'low', 'info')),
    confidence REAL CHECK(confidence >= 0 AND confidence <= 1),
    semantic_similarity REAL CHECK(semantic_similarity >= 0 AND semantic_similarity <= 1),
    description TEXT,
    conflicting_elements JSONB,
    author_a TEXT,
    author_b TEXT,
    is_self_contradiction BOOLEAN DEFAULT FALSE,
    date_a TEXT,
    date_b TEXT,
    temporal_gap_days INTEGER,
    legal_significance TEXT,
    relevant_case_law JSONB,
    recommended_action TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    detection_model TEXT,
    reviewed BOOLEAN DEFAULT FALSE,
    reviewer_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_contradictions_case ON contradictions(case_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_type ON contradictions(contradiction_type);

-- Bias Indicators
CREATE TABLE IF NOT EXISTS bias_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id),
    professional_id UUID REFERENCES professionals(id),
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
    z_score REAL,
    p_value REAL,
    baseline_mean REAL,
    baseline_std REAL,
    baseline_id TEXT,
    direction TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bias_case ON bias_indicators(case_id);

-- Arguments (Toulmin)
CREATE TABLE IF NOT EXISTS arguments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    claim_text TEXT NOT NULL,
    grounds JSONB,
    warrant TEXT,
    warrant_rule_id TEXT,
    backing JSONB,
    qualifier TEXT,
    rebuttal JSONB,
    falsifiability_conditions JSONB,
    missing_evidence JSONB,
    alternative_explanations JSONB,
    confidence_lower REAL,
    confidence_upper REAL,
    confidence_mean REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_arguments_case ON arguments(case_id);

-- Legal Rules
CREATE TABLE IF NOT EXISTS legal_rules (
    rule_id TEXT PRIMARY KEY,
    short_name TEXT NOT NULL,
    full_citation TEXT NOT NULL,
    text TEXT,
    category TEXT CHECK(category IN ('welfare', 'threshold', 'evidence', 'professional', 'procedural')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bias Baselines
CREATE TABLE IF NOT EXISTS bias_baselines (
    baseline_id TEXT PRIMARY KEY,
    doc_type TEXT NOT NULL,
    metric TEXT NOT NULL,
    mean REAL NOT NULL,
    std_dev REAL NOT NULL,
    corpus_size INTEGER DEFAULT 100,
    source TEXT CHECK(source IN ('empirical', 'estimated', 'calibrated')) DEFAULT 'estimated',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(doc_type, metric)
);

-- Analysis Runs
CREATE TABLE IF NOT EXISTS analysis_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    run_type TEXT CHECK(run_type IN ('full', 'incremental', 'targeted', 'document', 'bias', 'claims')),
    status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed', 'cancelled')) DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    documents_analyzed INTEGER DEFAULT 0,
    claims_extracted INTEGER DEFAULT 0,
    biases_detected INTEGER DEFAULT 0,
    model_used TEXT,
    prompt_version TEXT,
    total_tokens INTEGER DEFAULT 0,
    cost_estimate REAL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runs_case ON analysis_runs(case_id);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_cases_timestamp
    BEFORE UPDATE ON cases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Row Level Security (optional but recommended)
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE claims ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your auth setup)
-- Example: Allow authenticated users to read all data
-- CREATE POLICY "Allow read access" ON cases FOR SELECT USING (true);
