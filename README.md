# 🛡️ MASVS Audit Copilot

AI-powered mobile application security audit tool that transforms raw security analysis artifacts into structured, professional MASVS v2 audit reports.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend (Vite)                    │
│  ┌──────────┐ ┌───────────┐ ┌──────────────┐ ┌───────────┐ │
│  │  Upload   │ │ Dashboard │ │ Report View  │ │  Policy   │ │
│  │  Page     │ │  (SSE)    │ │  (HTML/PDF)  │ │ Explorer  │ │
│  └──────────┘ └───────────┘ └──────────────┘ └───────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────────┐  │
│  │ Parsers │→│ Mapper  │→│ Scorer  │→│ LLM + RAG Engine │  │
│  │ Module  │ │ Module  │ │ Module  │ │ (Claude + Chroma) │  │
│  └─────────┘ └─────────┘ └─────────┘ └──────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Report Generator (Jinja2 → HTML/PDF)     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ SQLite   │ │ ChromaDB │ │ Job Queue│                    │
│  │ (ORM)    │ │ (Vectors)│ │ (async)  │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Features

- **Multi-source parsing**: MobSF JSON, JADX Java, Burp Suite XML, AndroidManifest.xml
- **MASVS v2.1.0 mapping**: Rule-based + LLM semantic mapping to MASVS/MASWE/MASTG
- **Criticality scoring**: Impact × Exploitability × Exposure model
- **RAG-augmented remediation**: Context-aware fix guidance from OWASP knowledge base
- **Professional reports**: HTML, PDF, and JSON policy output
- **Real-time pipeline**: SSE streaming of analysis progress
- **Demo mode**: Bundled sample data for instant testing

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) Google Gemini API key for LLM features

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure (optional — works without API key in demo mode)
cp ../.env.example .env
# Edit .env to add GEMINI_API_KEY

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Demo Mode

```bash
cd backend
python -m app.demo
```

### Docker

```bash
# Copy and configure env
cp .env.example .env

# Start all services
docker-compose up -d

# Access: http://localhost:5173 (frontend) / http://localhost:8000 (API)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze` | Upload files, start analysis pipeline |
| GET | `/api/jobs/{id}` | Get job status |
| GET | `/api/jobs/{id}/events` | SSE pipeline progress stream |
| GET | `/api/reports/{id}` | Get full JSON report |
| GET | `/api/reports/{id}/html` | Download HTML report |
| GET | `/api/reports/{id}/pdf` | Download PDF report |
| GET | `/api/reports/{id}/policy` | Download JSON policy |
| POST | `/api/findings/{id}/override` | Manual score override |
| GET | `/api/knowledge/search` | RAG search endpoint |
| GET | `/api/health` | Health check |

## Pipeline Stages

1. **Parsing** → Extract findings from uploaded artifacts
2. **Mapping** → Map findings to MASVS/MASWE/MASTG controls
3. **Scoring** → Compute criticality scores (Impact × Exploitability × Exposure)
4. **Deduplication** → Merge duplicate findings via LLM
5. **LLM Enrichment** → Generate remediation guidance with RAG context
6. **Report Generation** → Produce HTML/PDF/JSON reports

## Testing

```bash
cd backend
pytest tests/ -v
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, TailwindCSS |
| Backend | FastAPI, Python 3.11+ |
| LLM | Google Gemini API |
| Vector DB | ChromaDB (persistent) |
| Reports | Jinja2 (HTML), WeasyPrint (PDF) |
| Database | SQLite / SQLAlchemy |

## License

MIT
