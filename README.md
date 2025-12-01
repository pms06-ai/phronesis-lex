# Phronesis LEX v2

**Forensic Case Intelligence Platform for UK Family Court Proceedings**

A subscription-powered intelligent document analysis system designed for single-user deployment. Leverages AI subscriptions (Claude, ChatGPT, Grok, Perplexity, etc.) via copy-paste workflow instead of API calls.

## Features

### Document Analysis
- **Claim Extraction**: Extract factual claims from legal documents
- **Document Summarization**: Structured summaries with party identification
- **Credibility Assessment**: Analyze witness statement credibility indicators
- **Timeline Extraction**: Build chronological timelines from multiple documents

### Forensic Intelligence
- **Contradiction Detection**: Cross-reference claims to find inconsistencies
- **Bias Analysis**: Statistical detection of language and reporting bias
- **Legal Framework Analysis**: Apply UK Family Court legal principles (Children Act 1989, Re B, Lucas Direction)

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

### Backend

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

### Prompt Generation (AI Workflow)
- `GET /api/prompts/types` - List available prompt types
- `POST /api/prompts/generate/claim-extraction` - Generate claim extraction prompt
- `POST /api/prompts/generate/document-summary` - Generate summary prompt
- `POST /api/prompts/generate/credibility-assessment` - Generate credibility prompt
- `POST /api/prompts/generate/contradiction-analysis` - Compare two claims
- `POST /api/prompts/generate/timeline` - Extract timeline from documents
- `POST /api/prompts/generate/legal-framework` - Legal framework analysis

### Response Parsing
- `POST /api/prompts/parse` - Parse AI response and import data
- `POST /api/prompts/parse/batch` - Parse multiple responses
- `GET /api/prompts/workflow-status/{case_id}` - Get workflow progress

### Analysis
- `GET /api/cases/{case_id}/contradictions` - Detect contradictions
- `GET /api/cases/{case_id}/bias-report` - Statistical bias report
- `POST /api/cases/{case_id}/generate-arguments` - Generate Toulmin arguments

## Legal Framework

Built-in support for UK Family Court legal principles:
- **Children Act 1989** - Welfare checklist (s.1(3))
- **Re B [2013] UKSC 33** - Balance of probabilities standard
- **Lucas Direction** - Proper approach to lies and inconsistencies
- **Re H-C [2016]** - Evidential approach to fact-finding

## License

Private use only.
