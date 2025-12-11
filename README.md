# Phronesis LEX v5.0

[![License: Private](https://img.shields.io/badge/License-Private-red.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![Deployment: Railway](https://img.shields.io/badge/Deployed%20on-Railway-purple.svg)](https://railway.app)

## Forensic Case Intelligence Platform for Legal Proceedings

A professional-grade intelligent document analysis system designed for legal case management. Combines AI-powered analysis (Claude, ChatGPT, Grok) with forensic detection engines for contradiction analysis, bias detection, and evidence tracking.

## Core Features

### 1. Advanced Contradiction Detection (8 Types)

Revolutionary systematic cross-referencing of claims to detect:

1. **DIRECT** - Opposite assertions about the same subject
2. **TEMPORAL** - Events that can't both be true given timeline constraints
3. **SELF_CONTRADICTION** - Same author contradicting themselves (most legally significant)
4. **MODALITY_SHIFT** - Allegations treated as established facts without proof
5. **VALUE** - Different numbers/values for the same attribute
6. **ATTRIBUTION** - Disputes about who said/did what
7. **QUOTATION** - Misrepresented quotes across documents
8. **OMISSION** - Material context omitted (detected via asymmetric reporting)

### 2. Documentary Analysis

Professional broadcast analysis capabilities:

- **Video Processing**: Automated face detection, OCR, and speaker diarization
- **Timing Analysis**: Trace suspect-framing vs exculpatory evidence timing (27:1 ratios)
- **Delay Detection**: Identify critical information delays (e.g., 45:43 minute delays)
- **Reference Tracking**: Track mentions of specific individuals across audio/visuals
- **Quantifiable Metrics**: Statistical bias scoring with z-scores and p-values

### 3. Document Analysis & Claim Extraction

- **Epistemic Claim Extraction**: Extract claims with modality, certainty, and attribution tracking
- **Document Summarization**: Structured summaries with party identification
- **Credibility Assessment**: Analyze witness statement credibility indicators per Lucas direction
- **Timeline Extraction**: Build chronological timelines from multiple documents
- **Entity Resolution**: Fuzzy matching for entity identification across documents

### 4. Legal Framework Integration (50+ Provisions)

Built-in UK Family Court legal rules and case law:

**Children Act 1989:**

- Section 1(1): Paramountcy Principle
- Section 1(3): Welfare Checklist (7 factors)
- Section 31(2): Threshold Criteria

**Practice Directions:**

- PD12J: Domestic Abuse
- PD12B: Child Arrangements Programme

**Case Law:**

- **Re B [2008] UKHL 35** - Balance of probabilities standard
- **Re H-C [2016] EWCA Civ 136** - Lucas direction on lies
- **Re A [2015] EWFC 11** - Holistic evidence evaluation
- **Re W [2010]** - Lucas direction application

### 5. Statistical Bias Detection

- **Z-score Analysis**: Statistical significance testing for bias indicators
- **Baseline Calibration**: Compare against document type baselines
- **Language Bias**: Detect prejudicial language patterns
- **Interview Disparity**: Quantify imbalanced representation
- **Temporal Bias**: Identify timing-based framing patterns

### 6. Evidence & Violation Tracking

- **Evidence Gap Analysis**: Track "Have vs. Need" evidence items
- **Violation Assessment**: Honest strength scoring (Strong/Moderate/Weak/Unsubstantiated)
- **Priority Management**: Critical, High, Medium, Low priority tracking
- **Unlock Potential Mapping**: Identify what each evidence piece enables

### AI Subscription Workflow

Instead of expensive API calls, this platform uses a copy-paste workflow:

1. Generate optimized prompts from your documents
2. Copy to your AI subscription (Claude, ChatGPT, Grok, etc.)
3. Paste the AI response back to import structured data

**Supported Platforms**: Claude, ChatGPT, Grok, Perplexity, Le Chat, Venice AI

## Architecture

```
phronesis-lex-v2/
├── backend/                 # FastAPI backend
│   ├── app.py              # Main API application
│   ├── auth.py             # JWT authentication
│   ├── audit.py            # Audit logging
│   ├── config.py           # Configuration
│   ├── db/                 # Database layer (SQLite/aiosqlite)
│   ├── fcip/               # Forensic Case Intelligence Platform engines
│   │   ├── engines/        # Analysis engines
│   │   │   ├── argumentation.py    # Toulmin argument generation
│   │   │   ├── bias.py             # Statistical bias detection
│   │   │   ├── contradiction.py    # Contradiction detection
│   │   │   ├── entity_resolution.py # Entity matching
│   │   │   └── temporal.py         # Timeline parsing
│   │   ├── models/         # Domain models
│   │   └── services/       # Analysis services
│   ├── prompts/            # AI subscription workflow
│   │   ├── templates.py    # UK Family Court prompt templates
│   │   ├── generator.py    # Prompt generation
│   │   └── parser.py       # AI response parsing
│   └── services/           # Document processing, Claude service
│
└── frontend/               # React + TypeScript frontend
    ├── src/
    │   ├── pages/
    │   │   ├── AIWorkflow.tsx      # Prompt generation & response import
    │   │   ├── Contradictions.tsx  # Contradiction explorer
    │   │   ├── BiasAnalysis.tsx    # Bias detection dashboard
    │   │   └── ...
    │   ├── services/
    │   │   └── api.ts      # API client with auth
    │   └── components/
    └── package.json
```

## Quick Start

### Docker (Recommended)

To build the total functioning product including backend (FastAPI + all deps), frontend, and databases:

```bash
docker-compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Docs: `http://localhost:8000/docs`

### Manual Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Set environment variables (optional)
export AUTH_DISABLED=true  # For local development
export JWT_SECRET_KEY=your-secret-key

# Run server
python app.py
```

Server runs at `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

## Authentication

Default credentials (for personal use):

- Username: `admin`
- Password: `phronesis2024`

Or set `AUTH_DISABLED=true` to skip authentication.

## API Endpoints

See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for complete API documentation.

### Core Endpoints

#### Cases

- `GET /api/cases` - List all cases
- `POST /api/cases` - Create new case
- `GET /api/cases/{case_id}` - Get case details with statistics

#### Documents

- `POST /api/cases/{case_id}/documents` - Upload document
- `GET /api/cases/{case_id}/documents` - List case documents
- `GET /api/documents/{doc_id}/text` - Get document full text

#### Analysis

- `POST /api/fcip/analyze/{doc_id}` - Full FCIP analysis with all engines
- `GET /api/cases/{case_id}/contradictions` - Detect all 8 contradiction types
- `GET /api/cases/{case_id}/bias-report` - Statistical bias analysis
- `POST /api/cases/{case_id}/generate-arguments` - Generate Toulmin arguments

#### Documentary Analysis

- `POST /api/fcip/documentary/analyze` - Analyze video for bias, timing, speaker patterns

#### Legal Framework

- `GET /api/legal-rules` - List 50+ legal provisions
- `GET /api/contradiction-types` - Get contradiction type definitions

#### AI Subscription Workflow

- `GET /api/prompts/types` - Available prompt types
- `POST /api/prompts/generate/*` - Generate prompts for AI platforms
- `POST /api/prompts/parse` - Parse AI responses back to structured data

## Included Legal Provisions

Built-in support for UK Family Court legal principles:

- **Children Act 1989** - Welfare checklist (s.1(3)), Paramountcy (s.1(1)), Threshold (s.31(2))
- **Re B [2008] UKHL 35** - Balance of probabilities standard
- **Lucas Direction** - Proper approach to lies and inconsistencies
- **Re H-C [2016] EWCA Civ 136** - Evidential approach to fact-finding
- **Practice Directions** - PD12J (Domestic Abuse), PD12B (Child Arrangements)

## Documentation

Comprehensive documentation is available in the [docs](./docs) directory:

### Implementation & Architecture

- [**CLAUDE_CODE_IMPLEMENTATION_SPEC.md**](./docs/CLAUDE_CODE_IMPLEMENTATION_SPEC.md) - Complete technical specification for building the Phronesis system, including architecture, data structures, algorithms, and implementation phases
- [**HANDOFF_QUICK_REFERENCE.md**](./docs/HANDOFF_QUICK_REFERENCE.md) - Quick reference guide for understanding the workflow and key files

### Legal Analysis Framework

- [**PHRONESIS_VIOLATIONS_ANALYSIS.md**](./docs/PHRONESIS_VIOLATIONS_ANALYSIS.md) - Violation-centered analysis framework covering 12 specific violations across Ofcom, GDPR, and Defamation claims
- [**PHRONESIS_EVIDENCE_TRACKER.md**](./docs/PHRONESIS_EVIDENCE_TRACKER.md) - Evidence status tracker showing what evidence exists vs. what is needed for each claim

### Case Context

This system is designed to analyze broadcasting compliance violations in the documentary case:

**Case:** Stephen v Channel Four Television Corporation

**Key Features:**

- 12 violation categories assessed with honest evidence gap analysis
- Violation-first methodology (start with alleged violations → request evidence needed → assess strength)
- Quantifiable documentary analysis (27:1 suspect-framing ratio, 45:43 minute delay to exculpatory content)
- Suppression detection for available but omitted exculpatory evidence
- Strength assessment: STRONG / MODERATE / WEAK / UNSUBSTANTIATED

## License

Private use only.
