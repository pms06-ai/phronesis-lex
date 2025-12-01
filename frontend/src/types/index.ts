/**
 * TypeScript types for Phronesis LEX
 * Forensic Case Intelligence Platform v5.0
 */

// Case Types
export interface Case {
  id: string;
  reference: string;
  title: string | null;
  case_type: string;
  case_type_display: string;
  court: string | null;
  court_level: string;
  court_level_display: string;
  region: string | null;
  status: 'active' | 'pending' | 'closed' | 'archived';
  status_display: string;
  filing_date: string | null;
  next_hearing_date: string | null;
  final_hearing_date: string | null;
  applicants: any[];
  respondents: any[];
  children: any[];
  description: string | null;
  key_issues: string[];
  document_count: number;
  claim_count: number;
  contradiction_count: number;
  bias_signal_count: number;
  created_at: string;
  updated_at: string;
}

// Document Types
export interface Document {
  id: string;
  case: string;
  filename: string;
  original_filename: string;
  doc_type: string;
  doc_type_display: string;
  title: string | null;
  date_filed: string | null;
  author: string | null;
  author_role: string | null;
  organisation: string | null;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  status_display: string;
  page_count: number;
  word_count: number;
  claim_count: number;
  bias_signal_count: number;
  created_at: string;
}

// Claim Types
export interface Claim {
  id: string;
  case: string;
  document: string;
  source_document: string;
  document_type: string;
  claim_type: string;
  claim_text: string;
  source_quote: string | null;
  subject: string | null;
  predicate: string | null;
  object_value: string | null;
  modality: 'asserted' | 'reported' | 'alleged' | 'denied' | 'hypothetical';
  polarity: 'affirm' | 'negate';
  certainty: number;
  certainty_markers: string[];
  asserted_by: string | null;
  time_expression: string | null;
  time_start: string | null;
  time_end: string | null;
  page_number: number | null;
  paragraph_number: number | null;
  confidence: number;
  created_at: string;
}

// Contradiction Types
export interface Contradiction {
  id: string;
  case: string;
  contradiction_type: 'direct' | 'temporal' | 'self' | 'modality' | 'value' | 'attribution' | 'quotation' | 'omission';
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  claim_a: string;
  claim_a_text: string;
  claim_a_document_id: string;
  claim_a_document_name: string;
  claim_a_page: number | null;
  claim_a_author: string | null;
  claim_b: string;
  claim_b_text: string;
  claim_b_document_id: string;
  claim_b_document_name: string;
  claim_b_page: number | null;
  claim_b_author: string | null;
  description: string;
  legal_significance: string | null;
  recommended_action: string | null;
  confidence: number;
  semantic_similarity: number;
  temporal_conflict: boolean;
  same_author: boolean;
  resolved: boolean;
  resolution_note: string | null;
  resolved_at: string | null;
  created_at: string;
}

// Bias Signal Types
export interface BiasSignal {
  id: string;
  case: string;
  document: string;
  document_name: string;
  document_type: string;
  signal_type: 'certainty_language' | 'negative_attribution' | 'quantifier_extremity' | 'attribution_asymmetry';
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  metric_value: number;
  baseline_mean: number;
  baseline_std: number;
  z_score: number;
  p_value: number | null;
  direction: 'higher' | 'lower';
  description: string;
  baseline_id: string;
  baseline_source: string;
  created_at: string;
}

// Timeline Types
export interface TimelineEvent {
  id: string;
  case: string;
  document: string;
  source_document_name: string;
  event_date: string;
  event_type: string;
  description: string;
  significance: 'critical' | 'major' | 'routine' | 'minor';
  verified: boolean;
  conflicting_events: string[];
  participants: string[];
  location: string | null;
  created_at: string;
}

// Argument Types
export interface ToulminArgument {
  id: string;
  case: string;
  claim_text: string;
  grounds: string[];
  warrant: string;
  warrant_rule_id: string | null;
  warrant_rule_name: string | null;
  backing: string[];
  qualifier: string;
  rebuttal: string[];
  falsifiability_conditions: any[];
  missing_evidence: string[];
  alternative_explanations: string[];
  confidence_lower: number;
  confidence_upper: number;
  confidence_mean: number;
  created_at: string;
}

// Entity Types
export interface Entity {
  id: string;
  case: string;
  canonical_name: string;
  entity_type: string;
  aliases: string[];
  roles: string[];
  organisation: string | null;
  claim_count: number;
  sentiment_score: number | null;
  created_at: string;
}

// Legal Rule Types
export interface LegalRule {
  rule_id: string;
  short_name: string;
  full_citation: string;
  text: string;
  category: 'welfare' | 'threshold' | 'evidence' | 'professional' | 'procedural';
  keywords: string[];
}

// Analysis Run Types
export interface AnalysisRun {
  id: string;
  case: string;
  run_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
  documents_analyzed: number;
  claims_extracted: number;
  contradictions_found: number;
  biases_detected: number;
  error_message: string | null;
  model_used: string | null;
  total_tokens: number;
  estimated_cost: number;
  progress_percent: number;
  progress_message: string | null;
}

// Dashboard Types
export interface DashboardStats {
  total_cases: number;
  active_cases: number;
  total_documents: number;
  total_claims: number;
  total_contradictions: number;
  unresolved_contradictions: number;
  cases_by_type: Record<string, number>;
  recent_cases: Case[];
  upcoming_hearings: Case[];
}

// Case Stats Types
export interface CaseStats {
  documents: number;
  claims: number;
  timeline_events: number;
  bias_indicators: number;
  contradictions: number;
  entities: number;
  arguments: number;
  claims_by_type: Record<string, number>;
  claims_by_modality: Record<string, number>;
  contradictions_by_type: Record<string, number>;
  contradictions_by_severity: Record<string, number>;
  average_claim_certainty: number | null;
  self_contradictions: number;
  unresolved_contradictions: number;
  high_severity_biases: number;
}

// API Response Types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

