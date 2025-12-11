# Phronesis LEX API Reference

**Version:** 5.0.0
**Base URL:** `http://localhost:8000` (development) | `https://your-domain.railway.app` (production)
**API Documentation:** `/docs` (Swagger UI) | `/redoc` (ReDoc)

## Table of Contents

- [Authentication](#authentication)
- [Cases](#cases)
- [Documents](#documents)
- [Claims](#claims)
- [Contradictions](#contradictions)
- [Analysis Engines](#analysis-engines)
- [Legal Framework](#legal-framework)
- [Bias Detection](#bias-detection)
- [Documentary Analysis](#documentary-analysis)
- [AI Subscription Workflow](#ai-subscription-workflow)
- [Timeline & Events](#timeline--events)
- [Professionals](#professionals)
- [Rate Limiting](#rate-limiting)

---

## Authentication

All endpoints (except `/health` and `/`) require JWT authentication unless `AUTH_DISABLED=true` is set.

### POST /api/auth/token

Obtain JWT access token.

**Request:**
```json
{
  "username": "admin",
  "password": "phronesis2024"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2025-12-11T10:30:00Z"
}
```

**Usage:**
```bash
# Include in subsequent requests
curl -H "Authorization: Bearer {access_token}" http://localhost:8000/api/cases
```

### GET /api/auth/user

Get current authenticated user info.

**Response:**
```json
{
  "username": "admin",
  "is_active": true
}
```

---

## Cases

### GET /api/cases

List all cases with basic information.

**Response:**
```json
{
  "cases": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "reference": "FD25P12345",
      "title": "Stephen v Channel Four Television Corporation",
      "court": "Family Division",
      "case_type": "family",
      "status": "active",
      "created_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

### POST /api/cases

Create a new case.

**Request (Form Data):**
```
reference: "FD25P12345"
title: "Case Title"
court: "Family Division"
case_type: "family"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "reference": "FD25P12345",
  "message": "Case created successfully"
}
```

### GET /api/cases/{case_id}

Get detailed case information with statistics.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "reference": "FD25P12345",
  "title": "Stephen v Channel Four Television Corporation",
  "court": "Family Division",
  "case_type": "family",
  "status": "active",
  "created_at": "2025-12-01T10:00:00Z",
  "stats": {
    "documents": 45,
    "claims": 127,
    "timeline_events": 89,
    "bias_indicators": 34
  }
}
```

---

## Documents

### POST /api/cases/{case_id}/documents

Upload and process a document.

**Request (Multipart Form):**
```
file: <file upload>
folder: "Statements" (optional)
doc_type: "witness_statement" (optional)
```

**Response:**
```json
{
  "id": "doc-123",
  "filename": "witness_statement_ford.pdf",
  "word_count": 3542,
  "page_count": 12,
  "message": "Document uploaded and processed successfully"
}
```

**Supported Formats:** PDF, DOCX, TXT, RTF, ODT

### GET /api/cases/{case_id}/documents

List all documents for a case.

**Response:**
```json
{
  "documents": [
    {
      "id": "doc-123",
      "filename": "witness_statement_ford.pdf",
      "folder": "Statements",
      "doc_type": "witness_statement",
      "word_count": 3542,
      "page_count": 12,
      "processed_at": "2025-12-01T14:30:00Z",
      "ocr_quality": 0.98
    }
  ]
}
```

### GET /api/documents/{doc_id}

Get document metadata.

**Query Parameters:**
- `include_text` (boolean, default: false) - Include full extracted text

**Response:**
```json
{
  "id": "doc-123",
  "case_id": "case-456",
  "filename": "witness_statement_ford.pdf",
  "folder": "Statements",
  "doc_type": "witness_statement",
  "word_count": 3542,
  "page_count": 12,
  "processed_at": "2025-12-01T14:30:00Z",
  "ocr_quality": 0.98,
  "file_hash": "sha256:abc123..."
}
```

### GET /api/documents/{doc_id}/text

Get full extracted text from document.

**Response:**
```json
{
  "text": "Full document text here...",
  "word_count": 3542
}
```

---

## Claims

### GET /api/cases/{case_id}/claims

List all claims extracted from case documents.

**Query Parameters:**
- `claim_type` (optional) - Filter by claim type (assertion, obligation, denial, etc.)

**Response:**
```json
{
  "claims": [
    {
      "id": "claim-789",
      "case_id": "case-456",
      "document_id": "doc-123",
      "claim_type": "assertion",
      "claim_text": "Simon Ford stated that Stephen was uncooperative during visits",
      "claimant_capacity": "social_worker",
      "target_entity": "Stephen",
      "context": "Page 3, paragraph 2",
      "ai_extracted": true,
      "ai_confidence": 0.89,
      "modality": "asserted",
      "polarity": "affirm",
      "certainty": 0.75,
      "created_at": "2025-12-01T15:00:00Z",
      "source_document": "witness_statement_ford.pdf"
    }
  ]
}
```

---

## Contradictions

### GET /api/cases/{case_id}/contradictions

Detect contradictions across all claims in a case. This is the revolutionary core feature.

**Query Parameters:**
- `refresh` (boolean, default: false) - Re-run analysis even if cached

**Response:**
```json
{
  "case_id": "case-456",
  "source": "analysis",
  "total_contradictions": 23,
  "by_type": {
    "direct": 8,
    "temporal": 3,
    "self_contradiction": 5,
    "modality_shift": 4,
    "value": 2,
    "attribution": 1,
    "quotation": 0,
    "omission": 0
  },
  "by_severity": {
    "critical": 5,
    "high": 10,
    "medium": 6,
    "low": 2
  },
  "critical_count": 5,
  "self_contradiction_count": 5,
  "authors_with_self_contradictions": ["Simon Ford", "Dr. Smith"],
  "contradictions": [
    {
      "id": "contra-001",
      "type": "self_contradiction",
      "severity": "critical",
      "claim_a": {
        "id": "claim-101",
        "text": "Stephen attended all scheduled visits in March 2024",
        "source": "witness_statement_ford_v1.pdf",
        "author": "Simon Ford",
        "date": "2024-04-15"
      },
      "claim_b": {
        "id": "claim-102",
        "text": "Stephen failed to attend three visits in March 2024",
        "source": "witness_statement_ford_v2.pdf",
        "author": "Simon Ford",
        "date": "2024-06-20"
      },
      "same_author": true,
      "semantic_similarity": 0.85,
      "confidence": 0.92,
      "explanation": "Same witness provided contradictory statements about attendance",
      "legal_significance": "Self-contradiction raises serious credibility issues per Lucas direction",
      "recommended_action": "Cross-examine on the inconsistency; consider whether contradiction goes to heart of witness's account",
      "case_law_reference": "Re H-C [2016] EWCA Civ 136 (Lucas direction)"
    }
  ]
}
```

**Contradiction Types:**

1. **DIRECT** - Opposite assertions (A says X, B says not-X)
2. **TEMPORAL** - Timeline impossibilities
3. **SELF_CONTRADICTION** - Same author contradicting themselves (most significant)
4. **MODALITY_SHIFT** - Allegations treated as proven facts
5. **VALUE** - Different numbers for same thing
6. **ATTRIBUTION** - Dispute about who said/did what
7. **QUOTATION** - Misrepresented quotes
8. **OMISSION** - Material context missing

### GET /api/cases/{case_id}/contradiction-summary

Quick summary for dashboard display.

**Response:**
```json
{
  "case_id": "case-456",
  "total": 23,
  "analyzed": true,
  "by_severity": {
    "critical": 5,
    "high": 10,
    "medium": 6,
    "low": 2
  },
  "by_type": {
    "self_contradiction": 5,
    "direct": 8,
    "temporal": 3
  },
  "critical_issues": [
    {
      "id": "contra-001",
      "type": "self_contradiction",
      "explanation": "Same witness provided contradictory statements about attendance",
      "same_author": true
    }
  ]
}
```

### GET /api/contradiction-types

List all contradiction types with legal significance.

**Response:**
```json
{
  "types": [
    {
      "type": "self_contradiction",
      "severity": "critical",
      "case_law": "Re H-C [2016] EWCA Civ 136 (Lucas direction)",
      "explanation": "A witness contradicting their own prior statement raises serious credibility issues...",
      "recommended_action": "Cross-examine on the inconsistency; consider whether contradiction goes to heart of witness's account"
    }
  ]
}
```

### POST /api/claims/compare

Compare two specific claims for contradiction.

**Request (Form Data):**
```
claim_a_id: "claim-101"
claim_b_id: "claim-102"
```

**Response:**
```json
{
  "is_contradiction": true,
  "type": "self_contradiction",
  "severity": "critical",
  "confidence": 0.92,
  "semantic_similarity": 0.85,
  "same_author": true,
  "explanation": "Same witness provided contradictory statements",
  "legal_significance": "Self-contradiction raises serious credibility issues",
  "recommended_action": "Cross-examine on the inconsistency",
  "case_law_reference": "Re H-C [2016] EWCA Civ 136"
}
```

---

## Analysis Engines

### POST /api/fcip/analyze/{doc_id}

Run full FCIP v5.0 analysis on a document with all engines.

**Engines Included:**
- Epistemic claim extraction
- Entity resolution
- Temporal parsing
- Statistical bias detection
- Argument generation

**Response:**
```json
{
  "status": "completed",
  "doc_type": "witness_statement",
  "doc_type_confidence": 0.94,
  "results": {
    "claims_extracted": 45,
    "entities_found": 12,
    "timeline_events": 8,
    "bias_signals": 6
  },
  "extraction_prompt_hash": "sha256:def456..."
}
```

### POST /api/documents/{doc_id}/analyze

Run basic Claude AI analysis (legacy endpoint).

**Response:**
```json
{
  "run_id": "run-123",
  "status": "completed",
  "results": {
    "claims_extracted": 42,
    "events_extracted": 7,
    "issues_detected": 3,
    "entities_found": 10
  },
  "analysis": {
    "claims": [...],
    "timeline_events": [...],
    "potential_issues": [...],
    "entities": [...]
  }
}
```

### GET /api/cases/{case_id}/entity-graph

Get resolved entity graph showing professionals and aliases.

**Response:**
```json
{
  "case_id": "case-456",
  "nodes": [
    {
      "id": "prof-001",
      "name": "Simon Ford",
      "profession": "social_worker",
      "capacity": "LA_social_worker",
      "party": "Local Authority",
      "aliases": ["S. Ford", "Mr Ford", "SW Ford"]
    }
  ],
  "total_entities": 12,
  "total_aliases": 34
}
```

---

## Legal Framework

### GET /api/legal-rules

List all legal rules from the FCIP library (50+ provisions).

**Query Parameters:**
- `category` (optional) - Filter by category (welfare, threshold, evidence, professional, procedural)

**Response:**
```json
{
  "rules": [
    {
      "rule_id": "CA1989.s1.1",
      "short_name": "Paramountcy Principle",
      "full_citation": "Children Act 1989, Section 1(1)",
      "text": "When a court determines any question with respect to the upbringing of a child, the child's welfare shall be the court's paramount consideration.",
      "category": "welfare"
    },
    {
      "rule_id": "Re_B_2008",
      "short_name": "Re B Standard",
      "full_citation": "Re B [2008] UKHL 35",
      "text": "The standard of proof in care proceedings is the balance of probabilities...",
      "category": "evidence"
    }
  ]
}
```

### POST /api/cases/{case_id}/generate-arguments

Generate Toulmin argument structures from case claims.

**Request (Form Data):**
```
finding_type: "welfare"  # Options: welfare, threshold, credibility, expert, bias
```

**Response:**
```json
{
  "argument_id": "arg-001",
  "argument": {
    "claim": "Based on analysis of 45 claims regarding welfare",
    "grounds": ["Claim 1", "Claim 2", "Claim 3"],
    "warrant": "Section 1(3) of the Children Act 1989 requires the court to have regard to the welfare checklist",
    "warrant_rule_id": "CA1989.s1.3",
    "backing": ["Legislative authority", "Case precedent"],
    "qualifier": "On the balance of probabilities",
    "rebuttal": ["Alternative explanation 1", "Missing evidence: X"],
    "falsifiability_conditions": ["If evidence X is produced", "If witness Y testifies"],
    "confidence_bounds": {
      "lower": 0.65,
      "mean": 0.78,
      "upper": 0.88
    }
  }
}
```

### GET /api/cases/{case_id}/arguments

List all generated arguments for a case.

---

## Bias Detection

### GET /api/cases/{case_id}/bias-report

Get comprehensive statistical bias analysis.

**Response:**
```json
{
  "case_id": "case-456",
  "total_signals": 34,
  "by_severity": {
    "high": 8,
    "medium": 18,
    "low": 8
  },
  "by_type": {
    "language_bias": 12,
    "selective_reporting": 10,
    "temporal_framing": 6,
    "interview_disparity": 6
  },
  "statistical_summary": {
    "mean_z_score": 2.34,
    "max_z_score": 4.56,
    "signals_above_critical": 8,
    "signals_above_warning": 18
  },
  "signals": [
    {
      "id": "bias-001",
      "type": "interview_disparity",
      "severity": "high",
      "z_score": 4.56,
      "p_value": 0.0001,
      "direction": "negative",
      "description": "Interview time disparity: 100:0 (Ford vs Stephen)",
      "document_id": "doc-documentary"
    }
  ]
}
```

### GET /api/cases/{case_id}/biases

List all bias indicators for a case.

### GET /api/bias-baselines

List all bias detection baselines.

**Response:**
```json
{
  "baselines": [
    {
      "baseline_id": "witness_statement_negative_language",
      "doc_type": "witness_statement",
      "metric": "negative_language_rate",
      "mean": 0.15,
      "std_dev": 0.05,
      "source": "calibrated"
    }
  ]
}
```

### POST /api/bias-baselines

Create or update a bias baseline.

**Request (Form Data):**
```
doc_type: "witness_statement"
metric: "negative_language_rate"
mean: 0.15
std_dev: 0.05
```

---

## Documentary Analysis

### POST /api/fcip/documentary/analyze

Start background video analysis task.

**Request (Form Data):**
```
video_path: "/path/to/documentary.mp4"
output_dir: "/path/to/output" (optional)
refs_dir: "/path/to/reference/images" (optional)
```

**Response:**
```json
{
  "message": "Analysis started in background",
  "video": "/uploads/documentary.mp4",
  "output_directory": "/uploads/analysis/20251210_143000",
  "status": "processing"
}
```

**Analysis Includes:**
- Face detection and recognition
- OCR text extraction from video frames
- Speaker diarization (who spoke when)
- Temporal bias analysis
- Suspect-framing ratio calculation
- Critical information delay detection

**Output Files:**
- `analysis_report.json` - Complete analysis results
- `frames/` - Extracted frames with faces/text
- `transcripts/` - Audio transcription
- `timing_analysis.json` - Temporal bias metrics

---

## AI Subscription Workflow

The copy-paste workflow for using AI subscriptions (Claude, ChatGPT, Grok, etc.) without API costs.

### GET /api/prompts/types

List available prompt types.

**Response:**
```json
{
  "types": [
    {
      "type": "claim_extraction",
      "description": "Extract factual claims from legal documents"
    },
    {
      "type": "document_summary",
      "description": "Generate structured summary with party identification"
    },
    {
      "type": "credibility_assessment",
      "description": "Analyze credibility indicators per Lucas direction"
    },
    {
      "type": "contradiction_analysis",
      "description": "Compare two claims for contradictions"
    },
    {
      "type": "timeline_extraction",
      "description": "Extract chronological events from documents"
    },
    {
      "type": "legal_framework",
      "description": "Apply legal rules to case situation"
    }
  ],
  "workflow": {
    "description": "Generate prompts here, copy to your AI platform, paste response back to parse",
    "supported_platforms": ["Claude", "ChatGPT", "Grok", "Perplexity", "Le Chat", "Venice AI"]
  }
}
```

### POST /api/prompts/generate/claim-extraction

Generate prompt for claim extraction.

**Request (Form Data):**
```
doc_id: "doc-123"
```

**Response:**
```json
{
  "prompt_id": "prompt-456",
  "prompt_type": "claim_extraction",
  "document": "witness_statement_ford.pdf",
  "full_prompt": "You are a legal analyst extracting claims from documents...\n\n[Full optimized prompt]",
  "estimated_tokens": 15000,
  "recommended_platforms": ["Claude", "ChatGPT", "Grok"],
  "notes": "Optimized for UK Family Court proceedings",
  "instructions": "Copy 'full_prompt' to your AI platform, then use /api/prompts/parse with the response"
}
```

### POST /api/prompts/generate/document-summary

Generate prompt for document summarization.

### POST /api/prompts/generate/credibility-assessment

Generate prompt for credibility assessment.

**Request (Form Data):**
```
doc_id: "doc-123"
author: "Simon Ford"
document_type: "statement"  # Options: statement, report, letter, email
```

### POST /api/prompts/generate/contradiction-analysis

Generate prompt to analyze contradictions between two claims.

**Request (Form Data):**
```
claim_a_id: "claim-101"
claim_b_id: "claim-102"
```

### POST /api/prompts/generate/timeline

Generate prompt to extract timeline.

**Request (Form Data):**
```
case_id: "case-456"
doc_ids: "doc-1,doc-2,doc-3"  # Comma-separated, or omit for all docs
```

### POST /api/prompts/generate/legal-framework

Generate prompt for legal framework analysis.

**Request (Form Data):**
```
case_id: "case-456"
situation: "Local authority alleges failure to engage with services"
```

### POST /api/prompts/parse

Parse AI response back into structured data.

**Request (Form Data):**
```
response_text: "{AI response JSON here}"
prompt_type: "claim_extraction"
case_id: "case-456" (optional, for auto-import)
doc_id: "doc-123" (optional)
```

**Response:**
```json
{
  "success": true,
  "prompt_type": "claim_extraction",
  "parsed_at": "2025-12-10T15:30:00Z",
  "warnings": [],
  "stored": {
    "claims": 42,
    "events": 7,
    "other": 0
  },
  "data": {
    "claims": [...],
    "summary": null,
    "contradiction": null
  }
}
```

### POST /api/prompts/parse/batch

Parse multiple AI responses at once.

**Request (Form Data):**
```
responses: '[{"response_text": "...", "prompt_type": "claim_extraction", "doc_id": "doc-1"}, ...]'
case_id: "case-456"
```

### GET /api/prompts/workflow-status/{case_id}

Get workflow progress and recommendations.

**Response:**
```json
{
  "case_id": "case-456",
  "status": {
    "documents": 45,
    "claims_total": 127,
    "claims_imported": 85,
    "timeline_events": 89,
    "contradictions_analyzed": 23
  },
  "workflow_progress": {
    "documents_uploaded": true,
    "claims_extracted": true,
    "timeline_built": true,
    "contradictions_analyzed": true
  },
  "recommended_next_steps": [
    {
      "priority": 1,
      "action": "Generate credibility assessments for key documents",
      "endpoint": "POST /api/prompts/generate/credibility-assessment"
    }
  ]
}
```

---

## Timeline & Events

### GET /api/cases/{case_id}/timeline

Get chronological timeline for a case.

**Response:**
```json
{
  "events": [
    {
      "id": "event-001",
      "case_id": "case-456",
      "event_date": "2024-03-15",
      "event_type": "visit",
      "description": "Social worker visit to family home",
      "source_document_id": "doc-123",
      "source_document": "witness_statement_ford.pdf",
      "significance": "routine"
    }
  ]
}
```

### GET /api/cases/{case_id}/deadline-alerts

Get deadline alerts for case.

**Response:**
```json
{
  "alerts": [
    {
      "id": "alert-001",
      "case_id": "case-456",
      "deadline_date": "2025-12-20",
      "deadline_type": "filing",
      "description": "Response to application due",
      "severity": "high",
      "days_remaining": 10
    }
  ]
}
```

---

## Professionals

### GET /api/cases/{case_id}/professionals

List all professionals involved in a case.

**Response:**
```json
{
  "professionals": [
    {
      "id": "prof-001",
      "name": "Simon Ford",
      "normalized_name": "simon ford",
      "profession": "social_worker",
      "registration_body": "Social Work England",
      "registration_number": "SW12345",
      "capacity": "LA_social_worker",
      "party_represented": "Local Authority"
    }
  ]
}
```

### POST /api/professionals

Create a new professional record.

**Request (Form Data):**
```
name: "Simon Ford"
profession: "social_worker"
registration_body: "Social Work England" (optional)
registration_number: "SW12345" (optional)
```

---

## Utility Endpoints

### GET /

API root health check.

**Response:**
```json
{
  "service": "Phronesis LEX API",
  "status": "operational",
  "version": "5.0.0"
}
```

### GET /health

Detailed health check.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "ai_configured": true,
  "processing_capabilities": {
    "pdf": true,
    "docx": true,
    "ocr": true,
    "documentary_analysis": true
  },
  "timestamp": "2025-12-10T15:30:00Z"
}
```

### POST /api/upload

Upload a file to server.

**Request (Multipart Form):**
```
file: <file upload>
```

**Response:**
```json
{
  "filename": "20251210_153000_document.pdf",
  "original_filename": "document.pdf",
  "file_path": "/uploads/20251210_153000_document.pdf"
}
```

### GET /api/audit-logs

Get audit logs (admin only).

**Query Parameters:**
- `resource_type` (optional) - Filter by resource type
- `action` (optional) - Filter by action (LOGIN, CREATE, UPDATE, DELETE, ANALYZE)
- `limit` (integer, default: 100) - Number of logs to return

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": "2025-12-10T15:30:00Z",
      "user": "admin",
      "action": "ANALYZE",
      "resource_type": "document",
      "resource_id": "doc-123",
      "resource_name": "witness_statement_ford.pdf",
      "description": "Ran FCIP analysis",
      "ip_address": "192.168.1.100",
      "success": true,
      "error": null
    }
  ]
}
```

---

## Rate Limiting

Rate limits are applied to prevent abuse:

- **Login endpoint:** 10 requests per minute per IP
- **Upload endpoint:** 10 requests per minute per user
- **Analysis endpoints:** Default FastAPI limits
- **Other endpoints:** No explicit limits (rely on authentication)

**Rate Limit Headers:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1702397400
```

**Rate Limit Exceeded Response:**
```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds."
}
```

---

## Error Responses

All endpoints follow consistent error response format:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid username or password"
}
```

### 404 Not Found
```json
{
  "detail": "Case not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": "Document has no extracted text",
  "errors": ["Validation error details"]
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Analysis failed: [error details]"
}
```

### 503 Service Unavailable
```json
{
  "detail": "AI analysis not configured - missing API key"
}
```

---

## Data Models

### Claim
```json
{
  "id": "uuid",
  "case_id": "uuid",
  "document_id": "uuid",
  "claim_type": "assertion|obligation|denial|question",
  "claim_text": "string",
  "claimant_capacity": "string",
  "target_entity": "string",
  "context": "string",
  "modality": "asserted|alleged|denied|uncertain",
  "polarity": "affirm|negate",
  "certainty": 0.0-1.0,
  "certainty_markers": ["string"],
  "asserted_by": "string",
  "time_expression": "string",
  "ai_extracted": true|false,
  "ai_confidence": 0.0-1.0,
  "created_at": "timestamp"
}
```

### Contradiction
```json
{
  "id": "uuid",
  "case_id": "uuid",
  "claim_a_id": "uuid",
  "claim_b_id": "uuid",
  "contradiction_type": "direct|temporal|self_contradiction|modality_shift|value|attribution|quotation|omission",
  "severity": "critical|high|medium|low",
  "same_author": true|false,
  "semantic_similarity": 0.0-1.0,
  "confidence": 0.0-1.0,
  "explanation": "string",
  "legal_significance": "string",
  "recommended_action": "string",
  "case_law_reference": "string",
  "detection_method": "string",
  "created_at": "timestamp"
}
```

### BiasIndicator
```json
{
  "id": "uuid",
  "case_id": "uuid",
  "document_id": "uuid",
  "bias_type": "language_bias|selective_reporting|temporal_framing|interview_disparity",
  "severity": "high|medium|low",
  "evidence_text": "string",
  "z_score": -5.0 to 5.0,
  "p_value": 0.0-1.0,
  "baseline_mean": float,
  "baseline_std": float,
  "direction": "positive|negative|neutral",
  "created_at": "timestamp"
}
```

---

## Examples

### Complete Workflow Example

```bash
# 1. Authenticate
TOKEN=$(curl -X POST http://localhost:8000/api/auth/token \
  -d "username=admin&password=phronesis2024" | jq -r .access_token)

# 2. Create case
CASE_ID=$(curl -X POST http://localhost:8000/api/cases \
  -H "Authorization: Bearer $TOKEN" \
  -F "reference=FD25P12345" \
  -F "title=Test Case" | jq -r .id)

# 3. Upload document
DOC_ID=$(curl -X POST http://localhost:8000/api/cases/$CASE_ID/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@witness_statement.pdf" | jq -r .id)

# 4. Run FCIP analysis
curl -X POST http://localhost:8000/api/fcip/analyze/$DOC_ID \
  -H "Authorization: Bearer $TOKEN"

# 5. Detect contradictions
curl -X GET http://localhost:8000/api/cases/$CASE_ID/contradictions \
  -H "Authorization: Bearer $TOKEN"

# 6. Get bias report
curl -X GET http://localhost:8000/api/cases/$CASE_ID/bias-report \
  -H "Authorization: Bearer $TOKEN"
```

---

## Changelog

**v5.0.0** (2025-12-10)
- Added 8-type contradiction detection engine
- Integrated 50+ legal provisions
- Added documentary analysis capabilities
- Enhanced bias detection with z-scores
- Implemented AI subscription workflow
- Added evidence tracking endpoints

**v2.0.0** (2025-12-01)
- Initial production release
- Basic document analysis
- JWT authentication
- Docker deployment support

---

## Support

- **Documentation:** [docs/](../docs/)
- **API Explorer:** `/docs` (Swagger UI)
- **Issue Tracking:** Internal
- **License:** Private Use Only
