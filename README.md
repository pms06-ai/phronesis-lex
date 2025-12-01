# Phronesis LEX

## Forensic Case Intelligence Platform v5.0

A comprehensive forensic analysis platform for UK Family Court proceedings. Phronesis LEX combines AI-powered document analysis with legal reasoning frameworks to identify contradictions, detect bias, and generate structured legal arguments.

## 🎯 Key Features

### 🔍 Contradiction Detection Engine
- **Self-Contradiction Detection**: Identifies when the same author contradicts themselves (critical under the Lucas direction)
- **Cross-Document Analysis**: Compares claims across multiple documents
- **Temporal Impossibility Detection**: Flags timeline conflicts
- **Modality Confusion Detection**: Identifies when allegations are treated as established facts

### 📊 Statistical Bias Detection
- **Z-Score Analysis**: Compares document language against corpus baselines
- **Certainty Language Analysis**: Detects over-confident language patterns
- **Negative Attribution Detection**: Identifies disproportionately negative framing
- **Extreme Quantifier Detection**: Flags inappropriate use of "always/never/all/none"

### 📝 Claim Extraction
- **Epistemic Annotation**: Every claim tagged with modality (asserted/alleged/reported/denied)
- **Certainty Scoring**: 0-1 certainty score based on linguistic markers
- **Attribution Tracking**: Links claims to authors and sources
- **Subject-Predicate-Object Structure**: Enables systematic comparison

### ⚖️ Toulmin Argumentation Engine
- **Structured Legal Arguments**: Claim → Grounds → Warrant → Backing → Rebuttal
- **UK Legal Rules Integration**: CA 1989, PD12J, Re B, Lucas direction
- **Falsifiability Conditions**: Tests that would disprove each argument
- **Missing Evidence Detection**: Highlights gaps in supporting evidence

### 📅 Timeline Analysis
- **Chronological Event Extraction**: Builds case timeline from documents
- **Conflict Detection**: Identifies contradicting event accounts
- **Deadline Calculation**: UK court calendar integration

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/phronesis-lex.git
cd phronesis-lex

# Run setup script (Windows)
scripts\setup.bat

# Or manually:

# Backend setup
cd django_backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_legal_rules

# Frontend setup
cd ../frontend
npm install
```

### Running the Application

**Start Backend:**
```bash
cd django_backend
venv\Scripts\activate  # Windows
python manage.py runserver
```

**Start Frontend:**
```bash
cd frontend
npm run dev
```

Access the application at:
- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/

## 📁 Project Structure

```
phronesis-lex/
├── django_backend/          # Django REST API
│   ├── cases/              # Case management
│   ├── documents/          # Document handling
│   ├── analysis/           # Analysis engines
│   │   ├── models.py       # Claim, Contradiction, BiasSignal, etc.
│   │   ├── services/       # Detection engines
│   │   │   ├── claim_extraction.py
│   │   │   ├── contradiction_detection.py
│   │   │   ├── bias_detection.py
│   │   │   └── argument_generation.py
│   │   └── management/     # Django commands
│   └── requirements.txt
├── frontend/               # React + TypeScript frontend
│   ├── src/
│   │   ├── pages/         # Dashboard, Cases, Contradictions, etc.
│   │   ├── components/    # Layout, UI components
│   │   ├── services/      # API client
│   │   └── types/         # TypeScript definitions
│   └── package.json
└── scripts/               # Setup and run scripts
```

## 🔧 Configuration

Create a `.env` file in `django_backend/`:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# AI Integration (optional - for claim extraction)
ANTHROPIC_API_KEY=your-anthropic-api-key
CLAUDE_MODEL=claude-sonnet-4-20250514

# Database (default: SQLite)
DATABASE_URL=postgres://user:pass@localhost:5432/phronesis

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

## 📚 API Endpoints

### Cases
- `GET /api/cases/` - List cases
- `POST /api/cases/` - Create case
- `GET /api/cases/{id}/` - Get case details
- `GET /api/cases/{id}/stats/` - Get case statistics
- `POST /api/cases/{id}/analyze/` - Run full case analysis
- `GET /api/cases/dashboard/` - Dashboard statistics

### Documents
- `GET /api/cases/{id}/documents/` - List case documents
- `POST /api/documents/upload/` - Upload document
- `POST /api/documents/{id}/analyze/` - Analyze document

### Analysis
- `GET /api/cases/{id}/claims/` - List extracted claims
- `POST /api/cases/{id}/detect-contradictions/` - Run contradiction detection
- `GET /api/cases/{id}/contradictions/` - List contradictions
- `GET /api/cases/{id}/contradiction-summary/` - Contradiction statistics
- `POST /api/contradictions/{id}/resolve/` - Resolve contradiction
- `GET /api/cases/{id}/bias-report/` - Bias analysis report
- `GET /api/cases/{id}/timeline/` - Timeline events
- `POST /api/cases/{id}/generate-arguments/` - Generate Toulmin argument

### Reference
- `GET /api/legal-rules/` - UK legal rules library
- `GET /api/bias-baselines/` - Statistical baselines

## 🏛️ UK Legal Framework

Phronesis LEX is built around UK Family Court legal principles:

### Key Legislation
- **Children Act 1989** - Paramountcy principle (s1), welfare checklist (s1.3), threshold criteria (s31)
- **Family Procedure Rules 2010** - Procedural requirements
- **Practice Directions** - PD12J (domestic abuse), PD25C (expert evidence)

### Key Case Law
- **Re B [2008]** - Standard of proof (balance of probabilities, not possibility)
- **Re H-C [2016] / Lucas direction** - How to treat lies in evidence
- **Re A [2015]** - Holistic evidence assessment
- **Re J [2013]** - Burden of proof remains on the asserting party

## 🤝 Contributing

This project is designed for forensic legal analysis. Contributions should:
1. Follow UK Family Court legal principles
2. Include appropriate test coverage
3. Maintain the epistemic annotation framework
4. Document any new legal rules added

## ⚠️ Disclaimer

Phronesis LEX is a forensic analysis tool. It does not provide legal advice. All findings should be reviewed by qualified legal professionals before use in proceedings.

## 📄 License

MIT License - See LICENSE file for details.

