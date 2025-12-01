-- FCIP Schema Migration for Phronesis LEX
-- Adds tables and columns for FCIP algorithmic analysis engine
-- Run this after the main schema.sql

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- ============================================================================
-- MODIFY EXISTING TABLES
-- ============================================================================

-- Add FCIP columns to claims table
ALTER TABLE claims ADD COLUMN modality TEXT CHECK(modality IN (
    'asserted', 'reported', 'alleged', 'denied', 'hypothetical'
)) DEFAULT 'asserted';

ALTER TABLE claims ADD COLUMN polarity TEXT CHECK(polarity IN ('affirm', 'negate')) DEFAULT 'affirm';

ALTER TABLE claims ADD COLUMN certainty REAL CHECK(certainty >= 0 AND certainty <= 1) DEFAULT 0.5;

ALTER TABLE claims ADD COLUMN certainty_calibrated REAL CHECK(certainty_calibrated >= 0 AND certainty_calibrated <= 1);

ALTER TABLE claims ADD COLUMN certainty_markers TEXT;  -- JSON array

ALTER TABLE claims ADD COLUMN asserted_by TEXT;  -- Who made the claim

ALTER TABLE claims ADD COLUMN time_expression TEXT;  -- Verbatim temporal

ALTER TABLE claims ADD COLUMN time_start TEXT;  -- YYYY-MM-DD

ALTER TABLE claims ADD COLUMN time_end TEXT;  -- YYYY-MM-DD

ALTER TABLE claims ADD COLUMN time_precision TEXT CHECK(time_precision IN ('day', 'month', 'year', 'unknown')) DEFAULT 'unknown';

ALTER TABLE claims ADD COLUMN extraction_prompt_hash TEXT;  -- For reproducibility

ALTER TABLE claims ADD COLUMN extractor_model TEXT;

-- Add FCIP columns to documents table
ALTER TABLE documents ADD COLUMN provenance_hash TEXT;  -- SHA3-256

ALTER TABLE documents ADD COLUMN hash_algorithm TEXT DEFAULT 'sha3-256';

ALTER TABLE documents ADD COLUMN doc_type_confidence REAL CHECK(doc_type_confidence >= 0 AND doc_type_confidence <= 1);

-- Add FCIP columns to bias_indicators table
ALTER TABLE bias_indicators ADD COLUMN z_score REAL;

ALTER TABLE bias_indicators ADD COLUMN p_value REAL;

ALTER TABLE bias_indicators ADD COLUMN baseline_mean REAL;

ALTER TABLE bias_indicators ADD COLUMN baseline_std REAL;

ALTER TABLE bias_indicators ADD COLUMN baseline_id TEXT;

ALTER TABLE bias_indicators ADD COLUMN direction TEXT;  -- 'higher' or 'lower'

-- ============================================================================
-- NEW TABLES: FCIP Toulmin Arguments
-- ============================================================================

CREATE TABLE IF NOT EXISTS arguments (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,

    -- Toulmin structure
    claim_text TEXT NOT NULL,
    grounds TEXT,           -- JSON array of evidence points
    warrant TEXT,           -- Reasoning connecting evidence to claim
    warrant_rule_id TEXT,   -- Reference to legal rule
    backing TEXT,           -- JSON array of legal authorities
    qualifier TEXT CHECK(qualifier IN ('certainly', 'probably', 'possibly', 'tentatively')) DEFAULT 'probably',
    rebuttal TEXT,          -- JSON array of conditions invalidating claim

    -- Falsifiability
    falsifiability_conditions TEXT,  -- JSON array
    missing_evidence TEXT,           -- JSON array
    alternative_explanations TEXT,   -- JSON array

    -- Confidence bounds
    confidence_lower REAL CHECK(confidence_lower >= 0 AND confidence_lower <= 1),
    confidence_upper REAL CHECK(confidence_upper >= 0 AND confidence_upper <= 1),
    confidence_mean REAL CHECK(confidence_mean >= 0 AND confidence_mean <= 1),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_arguments_case ON arguments(case_id);
CREATE INDEX IF NOT EXISTS idx_arguments_rule ON arguments(warrant_rule_id);

-- ============================================================================
-- NEW TABLES: FCIP Legal Rules Library
-- ============================================================================

CREATE TABLE IF NOT EXISTS legal_rules (
    rule_id TEXT PRIMARY KEY,
    short_name TEXT NOT NULL,
    full_citation TEXT NOT NULL,
    rule_text TEXT NOT NULL,
    category TEXT CHECK(category IN ('welfare', 'threshold', 'evidence', 'professional', 'procedural')),
    jurisdiction TEXT DEFAULT 'England and Wales',
    effective_date DATE,
    superseded_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert core UK family law rules
INSERT OR IGNORE INTO legal_rules (rule_id, short_name, full_citation, rule_text, category) VALUES
('CA1989.s1.1', 'Paramountcy Principle', 'Children Act 1989, Section 1(1)',
 'When a court determines any question with respect to the upbringing of a child, the child''s welfare shall be the court''s paramount consideration.', 'welfare'),

('CA1989.s1.2', 'No Delay Principle', 'Children Act 1989, Section 1(2)',
 'The court shall have regard to the general principle that any delay in determining the question is likely to prejudice the welfare of the child.', 'welfare'),

('CA1989.s1.3', 'Welfare Checklist', 'Children Act 1989, Section 1(3)',
 'Court shall regard: wishes/feelings, needs, effect of change, background, harm, parental capability, powers available.', 'welfare'),

('CA1989.s31.2', 'Threshold Criteria', 'Children Act 1989, Section 31(2)',
 'Care order requires: child suffering/likely significant harm attributable to care not reasonable to expect.', 'threshold'),

('PD12J', 'Domestic Abuse PD', 'Practice Direction 12J FPR 2010',
 'Court must identify if domestic abuse raised and consider factual and welfare issues.', 'welfare'),

('Re_B_2008', 'Re B Standard', 'Re B [2008] UKHL 35',
 'Standard is balance of probabilities. Unproved facts must be left out entirely.', 'evidence'),

('Re_W_Lucas', 'Lucas Direction', 'R v Lucas [1981] QB 720; Re H-C [2016] EWCA Civ 136',
 'A lie is only probative of guilt if told to conceal the truth about the matter in issue.', 'evidence'),

('FJC_Guidance', 'Expert Witness Guidance', 'FJC Guidelines for Expert Witnesses',
 'Experts must be objective, independent, distinguish fact from opinion, acknowledge limitations.', 'professional'),

('SRA_Code', 'SRA Code of Conduct', 'SRA Standards and Regulations',
 'Solicitors must act in best interests of clients, with honesty and integrity.', 'professional'),

('BSB_Handbook', 'BSB Handbook', 'Bar Standards Board Handbook',
 'Barristers must not mislead the court. Owe duty to ensure proper administration of justice.', 'professional');

-- ============================================================================
-- NEW TABLES: FCIP Bias Baselines
-- ============================================================================

CREATE TABLE IF NOT EXISTS bias_baselines (
    baseline_id TEXT PRIMARY KEY,
    doc_type TEXT NOT NULL,
    metric TEXT NOT NULL,
    corpus_size INTEGER DEFAULT 0,
    mean REAL NOT NULL,
    std_dev REAL NOT NULL,
    source TEXT CHECK(source IN ('empirical', 'estimated', 'calibrated')) DEFAULT 'estimated',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(doc_type, metric)
);

-- Insert default baselines
INSERT OR IGNORE INTO bias_baselines (baseline_id, doc_type, metric, corpus_size, mean, std_dev, source) VALUES
('section_7_certainty', 'section_7_report', 'certainty_ratio', 100, 0.40, 0.15, 'estimated'),
('section_7_negative', 'section_7_report', 'negative_ratio', 100, 0.45, 0.12, 'estimated'),
('section_7_extreme', 'section_7_report', 'extreme_ratio', 100, 0.25, 0.10, 'estimated'),
('psychological_certainty', 'psychological_report', 'certainty_ratio', 100, 0.40, 0.15, 'estimated'),
('psychological_negative', 'psychological_report', 'negative_ratio', 100, 0.45, 0.12, 'estimated'),
('psychological_extreme', 'psychological_report', 'extreme_ratio', 100, 0.25, 0.10, 'estimated'),
('social_work_certainty', 'social_work_report', 'certainty_ratio', 100, 0.40, 0.15, 'estimated'),
('social_work_negative', 'social_work_report', 'negative_ratio', 100, 0.45, 0.12, 'estimated'),
('cafcass_certainty', 'cafcass_analysis', 'certainty_ratio', 100, 0.40, 0.15, 'estimated'),
('cafcass_negative', 'cafcass_analysis', 'negative_ratio', 100, 0.45, 0.12, 'estimated'),
('expert_certainty', 'expert_report', 'certainty_ratio', 100, 0.40, 0.15, 'estimated'),
('expert_negative', 'expert_report', 'negative_ratio', 100, 0.45, 0.12, 'estimated');

-- ============================================================================
-- NEW TABLES: FCIP Entity Aliases
-- ============================================================================

CREATE TABLE IF NOT EXISTS entity_aliases (
    alias_id TEXT PRIMARY KEY,
    professional_id TEXT NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    alias_text TEXT NOT NULL,
    match_type TEXT CHECK(match_type IN ('exact', 'fuzzy', 'role', 'learned')) DEFAULT 'exact',
    confidence REAL CHECK(confidence >= 0 AND confidence <= 1) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(professional_id, alias_text)
);

CREATE INDEX IF NOT EXISTS idx_aliases_professional ON entity_aliases(professional_id);
CREATE INDEX IF NOT EXISTS idx_aliases_text ON entity_aliases(alias_text);

-- ============================================================================
-- NEW TABLES: FCIP Deadline Alerts
-- ============================================================================

CREATE TABLE IF NOT EXISTS deadline_alerts (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    source_document_id TEXT REFERENCES documents(id),
    source_claim_id TEXT REFERENCES claims(id),

    deadline_text TEXT NOT NULL,           -- Original text
    deadline_date DATE,                    -- Calculated date
    anchor_date DATE,                      -- Reference date used
    working_days_only BOOLEAN DEFAULT FALSE,

    status TEXT CHECK(status IN ('pending', 'approaching', 'overdue', 'completed', 'dismissed')) DEFAULT 'pending',
    days_remaining INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deadlines_case ON deadline_alerts(case_id);
CREATE INDEX IF NOT EXISTS idx_deadlines_date ON deadline_alerts(deadline_date);
CREATE INDEX IF NOT EXISTS idx_deadlines_status ON deadline_alerts(status);

-- ============================================================================
-- NEW TABLES: FCIP Argument-Claim Links
-- ============================================================================

CREATE TABLE IF NOT EXISTS argument_claims (
    id TEXT PRIMARY KEY,
    argument_id TEXT NOT NULL REFERENCES arguments(id) ON DELETE CASCADE,
    claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    role TEXT CHECK(role IN ('ground', 'warrant_support', 'rebuttal_support')) DEFAULT 'ground',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(argument_id, claim_id)
);

CREATE INDEX IF NOT EXISTS idx_argclaims_argument ON argument_claims(argument_id);
CREATE INDEX IF NOT EXISTS idx_argclaims_claim ON argument_claims(claim_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

CREATE TRIGGER IF NOT EXISTS update_arguments_timestamp
    AFTER UPDATE ON arguments
    BEGIN
        UPDATE arguments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_baselines_timestamp
    AFTER UPDATE ON bias_baselines
    BEGIN
        UPDATE bias_baselines SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_deadlines_timestamp
    AFTER UPDATE ON deadline_alerts
    BEGIN
        UPDATE deadline_alerts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
