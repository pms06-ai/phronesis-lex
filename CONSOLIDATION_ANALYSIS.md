# Phronesis Project Consolidation Analysis

**Date**: 2025-12-10
**Objective**: Consolidate multiple Phronesis projects into a unified codebase

## Discovered Projects

### 1. phronesis-lex-1 (Current Directory)
**Location**: `C:\Users\pstep\phronesis-lex-1`
**Repository**: https://github.com/pms06-ai/phronesis-lex.git
**Branch**: main
**Status**: Active development with recent commits

**Stack**:
- Backend: **FastAPI** + SQLite/aiosqlite
- Frontend: **React + TypeScript** (Vite)
- Deployment: Docker + Railway

**Key Features**:
- AI Subscription Workflow (copy-paste instead of API calls)
- Document Analysis (claim extraction, summarization, credibility)
- Documentary Analysis (video processing, OCR, diarization)
- Contradiction Detection
- Bias Analysis (statistical z-score)
- Legal Framework Analysis (Children Act 1989, Re B, Lucas Direction)
- Toulmin Argumentation Engine
- Timeline Extraction

**Architecture Highlights**:
```
backend/
├── app.py (FastAPI main)
├── auth.py (JWT)
├── fcip/ (Forensic Case Intelligence Platform)
│   ├── engines/ (argumentation, bias, contradiction, entity_resolution, temporal)
│   ├── models/
│   └── services/
├── prompts/ (AI subscription workflow)
└── services/

frontend/
├── src/
│   ├── pages/ (AIWorkflow, Contradictions, BiasAnalysis, DocumentaryAnalysis, etc.)
│   ├── services/
│   └── components/
```

**Strengths**:
- Modern FastAPI backend (async support)
- AI subscription workflow (cost-effective)
- Documentary analysis capabilities
- Clean separation of concerns
- Docker deployment ready

### 2. phronesis-lex (Older Version)
**Location**: `C:\Users\pstep\phronesis-lex`
**Repository**: https://github.com/pms06-ai/phronesis-lex.git
**Branch**: migrate-fastapi-c0997 (not on main)
**Status**: Complex multi-structure repository

**Stack**:
- Backend: **Django REST Framework**
- Frontend: **React + TypeScript**
- Multiple overlapping structures (Phronesis/, unified-monorepo/, platform/)

**Key Features** (from README):
- Self-Contradiction Detection
- Cross-Document Analysis
- Temporal Impossibility Detection
- Modality Confusion Detection
- Statistical Bias Detection (Z-Score, Certainty Language, Negative Attribution)
- Claim Extraction with Epistemic Annotation
- Toulmin Argumentation Engine
- Timeline Analysis
- UK Legal Rules Integration

**Architecture**:
```
Phronesis/ (main working directory)
├── django_backend/
│   ├── cases/
│   ├── documents/
│   └── analysis/
│       ├── models.py
│       └── services/
├── frontend/

unified-monorepo/
├── apps/
│   ├── backend/ (Django)
│   └── frontend/ (React)
└── packages/
    └── tksa-core/

repos/ (reference copies)
scripts/ (analysis utilities)
```

**Strengths**:
- Mature Django ORM models
- Comprehensive contradiction detection
- Epistemic annotation framework (asserted/alleged/reported/denied)
- Statistical bias detection with baselines
- Timeline conflict detection
- UK legal rules database

**Weaknesses**:
- Confusing multiple overlapping structures
- Currently on migration branch (migrate-fastapi-c0997)
- Not actively developed

### 3. Phronesis (Minimal/Starter)
**Location**: `C:\Users\pstep\Phronesis`
**Repository**: https://github.com/pms06-ai/Phronesis.git
**Status**: Minimal project (only README.md)

**Assessment**: Not a significant codebase, can be archived.

### 4. Additional Documentation
**Location**: `C:\Users\pstep\OneDrive\Desktop\phronesis additional featuerws`

**Files**:
- CLAUDE_CODE_IMPLEMENTATION_SPEC.md
- HANDOFF_QUICK_REFERENCE.md
- PHRONESIS_EVIDENCE_TRACKER.md
- PHRONESIS_VIOLATIONS_ANALYSIS.md

**Assessment**: Important documentation that should be integrated into the consolidated project.

## Feature Comparison Matrix

| Feature | phronesis-lex-1 (FastAPI) | phronesis-lex (Django) |
|---------|---------------------------|------------------------|
| **Backend Framework** | FastAPI | Django REST |
| **Async Support** | ✅ Native | ⚠️ Limited |
| **Database** | SQLite/aiosqlite | SQLite/PostgreSQL |
| **AI Workflow** | Copy-paste subscription | API-based |
| **Claim Extraction** | ✅ | ✅ |
| **Contradiction Detection** | ✅ Basic | ✅ Advanced (self/cross/temporal/modality) |
| **Bias Analysis** | ✅ Z-score | ✅ Z-score + Certainty + Attribution |
| **Documentary Analysis** | ✅ Video/OCR/Diarization | ❌ |
| **Toulmin Arguments** | ✅ | ✅ |
| **Timeline Analysis** | ✅ | ✅ with conflict detection |
| **Epistemic Annotation** | ⚠️ Partial | ✅ Full (modality tagging) |
| **UK Legal Rules** | ✅ Framework | ✅ Database with seeding |
| **Docker Deployment** | ✅ | ✅ |
| **Frontend** | React+TS (Vite) | React+TS |

## Consolidation Strategy

### Recommended Approach: **FastAPI Base + Django Features**

**Primary Codebase**: Use `phronesis-lex-1` as the foundation

**Reasoning**:
1. Modern async FastAPI backend is better for long-running analysis tasks
2. AI subscription workflow is cost-effective for single-user deployment
3. Documentary analysis is unique and valuable
4. Clean, well-structured codebase
5. Already has Docker + Railway deployment working

### Features to Migrate from Django Version

#### 1. Enhanced Contradiction Detection
**From**: `phronesis-lex/Phronesis/django_backend/analysis/services/contradiction_detection.py`

Add to FastAPI:
- **Modality Confusion Detection**: When allegations are treated as established facts
- **Self-Contradiction vs Cross-Document**: Separate detection engines
- **Temporal Impossibility**: More sophisticated timeline conflict detection

#### 2. Epistemic Annotation System
**From**: `phronesis-lex` Django models

Enhance FastAPI claim extraction with:
- Explicit modality tagging: `ASSERTED`, `ALLEGED`, `REPORTED`, `DENIED`
- Certainty scores (0-1) based on linguistic markers
- Subject-Predicate-Object structure for systematic comparison

#### 3. Statistical Bias Detection Enhancements
**From**: Django's comprehensive bias detection

Add to FastAPI:
- Certainty Language Analysis (detecting over-confident patterns)
- Negative Attribution Detection (disproportionately negative framing)
- Extreme Quantifier Detection ("always/never/all/none")
- Bias baseline corpus comparison

#### 4. UK Legal Rules Database
**From**: Django's legal rules management

Add to FastAPI:
- Legal rules database schema
- Seed data for Children Act 1989, PD12J, Re B, Lucas direction
- API endpoints for legal rule lookup

#### 5. Timeline Conflict Detection
**From**: Django timeline analysis

Enhance FastAPI timeline with:
- Automatic conflict identification
- Event comparison across documents
- Temporal impossibility flagging

### Migration Plan

#### Phase 1: Analysis (✅ Current Phase)
- [x] Identify all projects
- [x] Compare features
- [x] Document consolidation strategy

#### Phase 2: Enhanced Data Models
- [ ] Add epistemic modality enum to FastAPI Claim model
- [ ] Add certainty_score field to claims
- [ ] Create ContradictionType enum (SELF, CROSS_DOCUMENT, TEMPORAL, MODALITY)
- [ ] Add LegalRule model and database seeding
- [ ] Create BiasBaseline model for corpus comparisons

#### Phase 3: Enhanced Detection Engines
- [ ] Migrate modality confusion detection
- [ ] Upgrade contradiction detection with self/cross/temporal separation
- [ ] Add certainty language analysis to bias detection
- [ ] Add negative attribution detection
- [ ] Add extreme quantifier detection

#### Phase 4: API Enhancements
- [ ] Add `/api/contradictions/by-type/{type}` endpoint
- [ ] Add `/api/bias/certainty-analysis` endpoint
- [ ] Add `/api/legal-rules` CRUD endpoints
- [ ] Add `/api/timeline/conflicts` endpoint

#### Phase 5: Frontend Integration
- [ ] Update TypeScript types for enhanced models
- [ ] Add epistemic modality filters to Contradictions page
- [ ] Add contradiction type breakdown visualization
- [ ] Add advanced bias analysis charts
- [ ] Add legal rules reference panel

#### Phase 6: Documentation Integration
- [ ] Move docs from "additional features" folder
- [ ] Update README with consolidated features
- [ ] Create API documentation with all endpoints
- [ ] Add implementation guides

#### Phase 7: Cleanup
- [ ] Archive C:\Users\pstep\Phronesis
- [ ] Archive or delete phronesis-lex after migration
- [ ] Consolidate all branches to main
- [ ] Create release tag v3.0

### Repository Structure (Post-Consolidation)

```
phronesis-lex/ (unified project)
├── backend/
│   ├── app.py
│   ├── models/
│   │   ├── claim.py (with epistemic modality)
│   │   ├── contradiction.py (with types)
│   │   ├── legal_rule.py
│   │   └── bias_baseline.py
│   ├── fcip/
│   │   ├── engines/
│   │   │   ├── argumentation.py
│   │   │   ├── bias.py (enhanced)
│   │   │   ├── contradiction.py (enhanced)
│   │   │   ├── entity_resolution.py
│   │   │   └── temporal.py (with conflict detection)
│   │   ├── models/
│   │   └── services/
│   ├── prompts/
│   ├── services/
│   │   └── documentary_analysis.py
│   └── seeds/
│       └── legal_rules.json
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── AIWorkflow.tsx
│   │   │   ├── Contradictions.tsx (enhanced)
│   │   │   ├── BiasAnalysis.tsx (enhanced)
│   │   │   ├── DocumentaryAnalysis.tsx
│   │   │   ├── LegalFramework.tsx
│   │   │   └── Timeline.tsx (with conflicts)
│   │   ├── services/
│   │   └── components/
│   └── package.json
├── docs/
│   ├── CLAUDE_CODE_IMPLEMENTATION_SPEC.md
│   ├── HANDOFF_QUICK_REFERENCE.md
│   ├── PHRONESIS_EVIDENCE_TRACKER.md
│   ├── PHRONESIS_VIOLATIONS_ANALYSIS.md
│   └── API_REFERENCE.md
├── docker-compose.yml
├── Dockerfile.backend
└── README.md
```

## Next Steps

1. **Review this analysis** - Confirm the consolidation approach
2. **Prioritize features** - Which Django features are most critical?
3. **Begin Phase 2** - Start with data model enhancements
4. **Incremental migration** - Migrate features one by one with testing
5. **Branch cleanup** - Merge cursor/claude agent branches after migration

## Questions for Review

1. Should we keep the AI subscription workflow or add API support?
2. Are there any features in the Django version we should exclude?
3. Should we maintain backward compatibility with Django database format?
4. What's the priority order for migrating features?

---

**Generated**: 2025-12-10
**Next Review**: After stakeholder feedback
