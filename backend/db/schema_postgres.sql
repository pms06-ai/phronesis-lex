-- Phronesis LEX Database Schema (PostgreSQL/Supabase)
-- Forensic Legal Investigation Platform
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cases (multi-case support)
CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference TEXT NOT NULL UNIQUE,
    title TEXT,
    court TEXT,
    case_type TEXT CHECK(case_type IN ('family', 'civil', 'criminal', 'tribunal', 'other')),
    status TEXT CHECK(status IN ('active', 'closed', 'appeal', 'archived')) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Professionals (all case participants)
CREATE TABLE IF NOT EXISTS professionals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    normalized_name TEXT,
    profession TEXT CHECK(profession IN (
        'judge', 'barrister', 'solicitor', 'social_worker',
        'psychologist', 'psychiatrist', 'cafcass_officer',
        'guardian', 'expert_witness', 'police_officer', 'other'
    )),
    qualifications JSONB DEFAULT '[]'::jsonb,
    registration_body TEXT,
    registration_number TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_professionals_normalized ON professionals(normalized_name);

-- Professional Capacities (who said what, in what role)
CREATE TABLE IF NOT EXISTS professional_capacities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    professional_id UUID NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    original_path TEXT,
    storage_path TEXT,  -- Supabase Storage path
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
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_documents_case ON documents(case_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_fulltext ON documents USING gin(to_tsvector('english', full_text));

-- Entity Extractions (NLP-extracted entities)
CREATE TABLE IF NOT EXISTS entity_extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    entity_text TEXT NOT NULL,
    normalized_text TEXT,
    confidence REAL CHECK(confidence >= 0 AND confidence <= 1),
    start_offset INTEGER,
    end_offset INTEGER,
    context TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_extractions_doc ON entity_extractions(document_id);
CREATE INDEX IF NOT EXISTS idx_extractions_type ON entity_extractions(entity_type);

-- Claims/Arguments (CRITICAL: First-class objects)
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
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_claims_case ON claims(case_id);
CREATE INDEX IF NOT EXISTS idx_claims_document ON claims(document_id);
CREATE INDEX IF NOT EXISTS idx_claims_claimant ON claims(claimant_professional_id);

-- Evidence Links (what supports each claim)
CREATE TABLE IF NOT EXISTS evidence_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    evidence_type TEXT CHECK(evidence_type IN (
        'document', 'testimony', 'expert_opinion', 'physical',
        'contemporaneous_record', 'third_party', 'admission', 'other'
    )),
    evidence_document_id UUID REFERENCES documents(id),
    evidence_description TEXT,
    evidence_strength TEXT CHECK(evidence_strength IN ('strong', 'moderate', 'weak', 'absent', 'contradictory')),
    is_cited BOOLEAN DEFAULT FALSE,
    is_available BOOLEAN DEFAULT TRUE,
    ai_assessment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_claim ON evidence_links(claim_id);

-- Competing Claims (claim vs counter-claim)
CREATE TABLE IF NOT EXISTS competing_claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_a_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    claim_b_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    relationship TEXT CHECK(relationship IN (
        'contradicts', 'supports', 'qualifies', 'supersedes',
        'partially_contradicts', 'contextualizes'
    )),
    resolution TEXT CHECK(resolution IN (
        'a_accepted', 'b_accepted', 'both_rejected', 'unresolved',
        'ignored', 'compromise', 'pending'
    )),
    resolved_by_professional_id UUID REFERENCES professionals(id),
    resolution_document_id UUID REFERENCES documents(id),
    resolution_reasoning TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK(claim_a_id != claim_b_id)
);

CREATE INDEX IF NOT EXISTS idx_competing_a ON competing_claims(claim_a_id);
CREATE INDEX IF NOT EXISTS idx_competing_b ON competing_claims(claim_b_id);

-- Timeline Events (temporal reconstruction)
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
    participants JSONB DEFAULT '[]'::jsonb,
    location TEXT,
    significance TEXT CHECK(significance IN ('critical', 'important', 'routine', 'minor')),
    verified BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_timeline_case ON timeline_events(case_id);
CREATE INDEX IF NOT EXISTS idx_timeline_date ON timeline_events(event_date);

-- Decision Points (what was known when decisions made)
CREATE TABLE IF NOT EXISTS decision_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    timeline_event_id UUID REFERENCES timeline_events(id),
    decision_maker_id UUID REFERENCES professionals(id),
    decision_text TEXT NOT NULL,
    decision_type TEXT CHECK(decision_type IN (
        'interim_order', 'final_order', 'direction', 'ruling',
        'recommendation', 'assessment_conclusion', 'finding', 'other'
    )),
    available_evidence JSONB DEFAULT '[]'::jsonb,
    unavailable_evidence JSONB DEFAULT '[]'::jsonb,
    alternatives_considered JSONB DEFAULT '[]'::jsonb,
    reasoning_given TEXT,
    ai_assessment TEXT,
    ai_reasonableness_score REAL CHECK(ai_reasonableness_score >= 0 AND ai_reasonableness_score <= 1),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_decisions_case ON decision_points(case_id);

-- Bias Indicators (detected cognitive biases)
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
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bias_case ON bias_indicators(case_id);
CREATE INDEX IF NOT EXISTS idx_bias_professional ON bias_indicators(professional_id);

-- Legal References (legislation, case law, standards)
CREATE TABLE IF NOT EXISTS legal_references (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    applies_to JSONB DEFAULT '[]'::jsonb,
    effective_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_legal_citation ON legal_references(citation);

-- Procedural Requirements (what should have happened)
CREATE TABLE IF NOT EXISTS procedural_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_reference_id UUID NOT NULL REFERENCES legal_references(id) ON DELETE CASCADE,
    requirement_text TEXT NOT NULL,
    applies_to_professional JSONB DEFAULT '[]'::jsonb,
    timing_requirement TEXT,
    mandatory BOOLEAN DEFAULT TRUE,
    evidence_of_compliance TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Compliance Checks (did they follow procedure?)
CREATE TABLE IF NOT EXISTS compliance_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    procedural_requirement_id UUID NOT NULL REFERENCES procedural_requirements(id),
    professional_id UUID REFERENCES professionals(id),
    compliant BOOLEAN,
    evidence_document_id UUID REFERENCES documents(id),
    non_compliance_description TEXT,
    impact_assessment TEXT,
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_compliance_case ON compliance_checks(case_id);

-- Analysis Runs (track AI analysis sessions)
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

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for cases updated_at
DROP TRIGGER IF EXISTS update_cases_updated_at ON cases;
CREATE TRIGGER update_cases_updated_at
    BEFORE UPDATE ON cases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) - Enable for production
-- ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
-- etc.

-- Grant permissions (adjust based on your Supabase setup)
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
