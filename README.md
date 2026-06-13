<![CDATA[<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/ChromaDB-Vector%20Store-4A90D9?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Gemini-2.0%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/License-Academic-green?style=for-the-badge" />
</p>

<h1 align="center">🔬 NovaRAG Research Studio</h1>
<h3 align="center">Enterprise-Grade AI Research Paper Summarizer & Report Generator</h3>
<p align="center"><em>Powered by Retrieval-Augmented Generation (RAG) with Grounded Citations & Hallucination Detection</em></p>

---

## 📖 Overview

**NovaRAG Research Studio** is an enterprise-grade, AI-powered research paper analysis platform that leverages Retrieval-Augmented Generation (RAG) to synthesize, summarize, and extract evidence from large corpora of academic research papers. Built with Streamlit, it provides a premium dark-themed dashboard for researchers, academics, and data scientists to interact with indexed PDF papers using natural language queries.

The system ingests PDF research papers into a ChromaDB vector database, applies semantic search with sentence-transformer embeddings, reranks retrieved passages using FlashRank, and generates grounded research syntheses using Google Gemini LLMs — all with robust hallucination detection, citation validation, and safety guardrails.

---

## 🎯 Problem Statement

Academic researchers face several critical challenges:

1. **Information Overload** — Keeping up with thousands of published research papers across domains like Healthcare AI, Drug Discovery, Federated Learning, and Explainable AI is overwhelming.
2. **Time-Intensive Literature Reviews** — Manually reading, cross-referencing, and synthesizing multi-paper reviews takes weeks or months.
3. **Hallucination Risks in AI Summaries** — Standard LLM-based summarizers often fabricate facts, statistics, and citations that don't exist in the source material.
4. **Lack of Verifiable Citations** — Most AI tools provide summaries without traceable references back to specific pages and passages.
5. **No Structured Report Generation** — Researchers need professional, print-ready reports with audit trails — not just raw text outputs.

---

## 💡 Solution

NovaRAG Research Studio solves these challenges with a **complete RAG pipeline** that:

- **Ingests & indexes** PDF research papers into a persistent ChromaDB vector store with page-level granularity
- **Classifies query intent** automatically (Factual QA, Document Summary, Research Synthesis, Evidence Extraction) using a rule-based classifier with hard-override detection
- **Retrieves & reranks** relevant passages using semantic embeddings (all-MiniLM-L6-v2) and FlashRank cross-encoder reranking
- **Generates grounded responses** via Google Gemini with strict system prompts that enforce citation requirements
- **Detects hallucinations** with a 3-tier scoring system (N-gram overlap, Entity verification, Citation coverage)
- **Validates citations** to ensure every [N] reference maps to a real retrieved source
- **Produces professional PDF reports** with cover pages, audit tables, academic references, and source excerpts
- **Enforces safety guardrails** against prompt injection, script injection, and out-of-scope queries

---

## ✨ Features

### Core Capabilities
| Feature | Description |
|---------|-------------|
| 🔬 **Academic Research Synthesis** | Synthesize multi-document research briefs with cited justifications across the entire corpus |
| 🎯 **Factual Question Answering** | Get short, direct answers to specific questions with source citations |
| 📄 **Single Document Summarization** | Generate comprehensive summaries scoped to a specific uploaded paper |
| 🔎 **Evidence Extraction** | Extract facts, page numbers, supporting quotes, and confidence scores |
| 📑 **Automated PDF Reports** | Generate professional, print-ready research briefs with cover pages and audit trails |
| 🛡️ **3-Tier Hallucination Detection** | N-gram overlap (40%), Entity verification (30%), Citation coverage (30%) |
| ⚡ **FlashRank Reranking** | Cross-encoder reranking for precise passage selection |
| 📤 **Corpus Management** | Upload, index, browse, and delete papers from the vector database |
| 📊 **Analytics Dashboard** | Track query history, groundedness scores, success rates, and category distributions |
| ⚙️ **Configurable Pipeline** | Tune retrieval depth, reranking count, chunk limits, and groundedness thresholds |

### Safety & Security
- **Input Guardrails** — Blocks prompt injection, script injection, and out-of-scope requests
- **Output Guardrails** — Detects hallucinated content using composite groundedness scoring
- **Citation Validation** — Verifies all inline citations [N] reference actual retrieved sources
- **Graceful Degradation** — Falls back to raw retrieved chunks when the LLM API is offline
- **Model Fallback Chain** — Automatically retries with alternative Gemini models on quota errors

### User Experience
- **Premium Dark Theme** — Glassmorphism, gradient animations, and micro-interactions
- **Animated Landing Page** — Typing animations, particle backgrounds, and staggered entrance effects
- **Sequential Loading Gateway** — Cinematic loader with progress bar and status messages
- **Interactive Demo Queries** — One-click sample queries on the landing page
- **10-Page Navigation** — Dashboard, Research Assistant, Upload, Browse, Synthesis, Evidence, Safety, Analytics, Reports, Settings

---

## 🛠️ Technology Stack

### Frontend
| Technology | Purpose |
|-----------|---------|
| **Streamlit** | Web application framework with reactive UI |
| **Custom CSS** | 600+ lines of premium dark-themed styling with glassmorphism, gradients, and animations |
| **Plotly** | Interactive charts (donut, area, bar, line, gauge) |
| **Google Fonts** | Inter, Orbitron, Space Grotesk, JetBrains Mono |
| **HTML/Markdown** | Custom card components, badges, metric displays |

### Backend
| Technology | Purpose |
|-----------|---------|
| **Python 3.10+** | Core application language |
| **Google Gemini API** | LLM generation (gemini-2.0-flash, gemini-2.5-flash-lite, gemini-2.5-flash) |
| **Sentence Transformers** | Local embedding model (all-MiniLM-L6-v2) |
| **FlashRank** | Cross-encoder passage reranking (ms-marco-MiniLM) |
| **ReportLab** | Professional PDF report generation with two-pass canvas |
| **PyPDF** | PDF text extraction and page-level parsing |

### Database
| Technology | Purpose |
|-----------|---------|
| **ChromaDB** | Persistent vector database for document embeddings |
| **SQLite** | Underlying storage engine for ChromaDB |

### AI Models Used
| Model | Role | Type |
|-------|------|------|
| **all-MiniLM-L6-v2** | Embedding generation | Local (Sentence Transformers) |
| **ms-marco-MiniLM-L-6-v2** | Passage reranking | Local (FlashRank) |
| **gemini-2.0-flash** | Primary LLM generation | Cloud API (Google) |
| **gemini-2.5-flash-lite** | Fallback LLM (quota overflow) | Cloud API (Google) |
| **gemini-2.5-flash** | Secondary fallback LLM | Cloud API (Google) |

### APIs Used
| API | Purpose |
|-----|---------|
| **Google Generative AI API** | Text generation, research synthesis, factual QA |
| **arXiv API** | Automated paper discovery and metadata retrieval |
| **Semantic Scholar API** | Extended paper search and metadata enrichment |
| **PubMed Central (PMC)** | Biomedical paper download support |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NovaRAG Research Studio                       │
│                    Streamlit Web Application                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────┐ │
│  │ Landing  │  │  Dashboard   │  │  Research     │  │Upload &│ │
│  │ Page     │→ │  Home        │  │  Assistant    │  │Corpus  │ │
│  └──────────┘  └──────────────┘  └──────┬───────┘  └───┬────┘ │
│                                         │               │       │
│  ┌──────────┐  ┌──────────────┐  ┌──────▼───────┐      │       │
│  │ Evidence │  │  Research    │  │   Intent      │      │       │
│  │ Extract  │  │  Synthesis   │  │   Classifier  │      │       │
│  └──────────┘  └──────────────┘  └──────┬───────┘      │       │
│                                         │               │       │
├─────────────────────────────────────────┼───────────────┼───────┤
│                 CORE ENGINE             │               │       │
│  ┌──────────────────────────────────────▼───────────────▼────┐  │
│  │                    RAG Pipeline                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │ Retrieve │→ │ Dedup &  │→ │ Rerank   │→ │ Generate │  │  │
│  │  │ (ChromaDB)│  │ Filter  │  │(FlashRank)│  │ (Gemini) │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐ │
│  │  Input        │  │  Output       │  │  Citation           │ │
│  │  Guardrails   │  │  Guardrails   │  │  Validator          │ │
│  │  (Safety)     │  │  (3-Tier)     │  │  (Coverage Check)   │ │
│  └───────────────┘  └───────────────┘  └─────────────────────┘ │
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐ │
│  │  PDF          │  │  Ingest       │  │  Paper              │ │
│  │  Generator    │  │  Engine       │  │  Downloader         │ │
│  │  (ReportLab)  │  │  (PyPDF)      │  │  (arXiv/S2/PMC)    │ │
│  └───────────────┘  └───────────────┘  └─────────────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                     │
│  ┌─────────────┐  ┌────────────┐  ┌──────────────────────────┐ │
│  │ ChromaDB    │  │ papers.csv │  │ papers/ (158 PDFs)       │ │
│  │ (Vector DB) │  │ (Metadata) │  │ reports/ (63 PDFs)       │ │
│  │ ~92MB       │  │ 62KB       │  │ chroma_db/ (SQLite)      │ │
│  └─────────────┘  └────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 RAG Workflow

The NovaRAG pipeline follows a **Retrieve → Deduplicate → Rerank → Generate → Verify** workflow:

### 1. 📤 Document Upload
Users upload PDF research papers through the **Upload & Corpus** page. Files are accepted in `.pdf` format and can be uploaded individually or in bulk batches.

### 2. 📝 Text Extraction
PyPDF extracts text page-by-page from each uploaded PDF. Each word is tagged with its source page number to enable page-level citations in generated reports.

### 3. ✂️ Chunking
Text is split into overlapping chunks using a sliding-window approach:
- **Chunk size**: ~562 words (~750 tokens)
- **Overlap**: ~94 words (~125 tokens)
- **Page tracking**: Each chunk records the page range it spans (e.g., "3-4")

### 4. 🧬 Embedding Generation
Each chunk is embedded using the **all-MiniLM-L6-v2** sentence-transformer model, which runs locally on CPU/GPU. This produces 384-dimensional dense vectors that capture semantic meaning.

### 5. 💾 Vector Database (ChromaDB)
Embedded chunks are upserted into a **persistent ChromaDB** collection with rich metadata:
- `document_id` — Unique hash-based identifier
- `title` — Source PDF filename
- `page_number` — Page range covered by the chunk
- `source` — Original file reference

### 6. 🔍 Similarity Search
When a user submits a query:
1. The query is embedded using the same all-MiniLM-L6-v2 model
2. ChromaDB performs approximate nearest-neighbor search
3. Up to `3 × top_k_retrieve` initial candidates are retrieved (default: 60)
4. Optional `document_id` filtering restricts results to a single paper

### 7. 🎯 Context Retrieval (Deduplication + Reranking)
Retrieved candidates undergo two-stage refinement:

**Stage A — Cross-Document Deduplication:**
- Papers are identified by normalized title and arXiv ID
- Maximum `max_chunks_per_doc` chunks kept per unique paper (default: 3)
- Prevents any single paper from dominating the context window

**Stage B — FlashRank Reranking:**
- The ms-marco-MiniLM cross-encoder scores each passage against the query
- Top `top_n_rerank` passages are selected (default: 7)
- Ensures the highest-relevance passages are used for generation

### 8. 📝 Answer Generation
The final context is sent to **Google Gemini** with intent-specific system prompts:

| Intent | System Prompt | Max Tokens | Temperature |
|--------|---------------|------------|-------------|
| `FACTUAL_QA` | Direct answer extraction | 300 | 0.05 |
| `DOCUMENT_SUMMARY` | Single-paper summary | 2,000 | 0.10 |
| `RESEARCH_SYNTHESIS` | Multi-paper synthesis | 2,000 | 0.10 |
| `EVIDENCE_EXTRACTION` | Fact + quote extraction | 1,000 | 0.05 |

Post-processing includes:
- Chain-of-thought leakage removal
- Citation format normalization ([N] style)
- Section header enforcement
- 3-tier groundedness scoring

---

## 📁 Folder Structure

```
NovaRAG-Research-Studio/
│
├── app.py                          # Main application shell & page router
├── rag_pipeline.py                 # Core RAG engine (retrieve → rerank → generate)
├── ingest.py                       # PDF ingestion, chunking, ChromaDB operations
├── guardrails.py                   # Input/output safety & 3-tier groundedness scoring
├── intent_classifier.py            # Rule-based query intent classification
├── pdf_generator.py                # Professional PDF report generation (ReportLab)
├── audit.py                        # Database auditing & metadata validation
│
├── download_papers.py              # arXiv paper downloader with fallback synthesis
├── download_real_papers.py         # Extended real paper downloader
├── download_weak_categories.py     # Targeted downloads for underrepresented categories
│
├── pages/                          # Streamlit page modules
│   ├── __init__.py
│   ├── landing.py                  # Premium animated entrance page & loader
│   ├── dashboard.py                # Home dashboard with metrics & charts
│   ├── research_assistant.py       # Main research query interface
│   ├── upload_corpus.py            # PDF upload & corpus management
│   ├── browse_papers.py            # Paper browser with category filtering
│   ├── research_synthesis.py       # Multi-paper synthesis workspace
│   ├── evidence_extraction.py      # Evidence extraction with confidence scoring
│   ├── safety_audit.py             # Safety & guardrails testing page
│   ├── analytics.py                # Query analytics & performance metrics
│   ├── reports.py                  # Report history & downloads
│   └── settings.py                 # API keys, model config, pipeline parameters
│
├── utils/                          # Shared utilities
│   ├── __init__.py
│   ├── theme.py                    # Full custom CSS theme (614 lines)
│   ├── components.py               # Reusable UI components (cards, badges, metrics)
│   ├── helpers.py                  # Data loading, categorization, enrichment
│   └── charts.py                   # Plotly chart builders (donut, area, bar, gauge)
│
├── papers/                         # Indexed research paper PDFs (158 files)
├── reports/                        # Generated PDF research reports (63 files)
├── chroma_db/                      # Persistent ChromaDB vector store (~92MB)
│   └── chroma.sqlite3
│
├── papers.csv                      # Paper metadata index (titles, authors, arXiv IDs)
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (GEMINI_API_KEY)
├── .gitignore                      # Git ignore rules
│
├── test_*.py                       # Test scripts (pipeline, guardrails, intent, etc.)
├── check_*.py                      # Diagnostic scripts
├── inspect_*.py                    # Database inspection utilities
├── run_*.py                        # Batch processing scripts
├── validate_*.py                   # Validation scripts
└── compile_final_pdf.py            # Final PDF compilation utility
```

---

## 🚀 Installation Guide

### Prerequisites
- **Python 3.10+** installed
- **Git** installed
- **Google Gemini API Key** (free tier available at [aistudio.google.com](https://aistudio.google.com))

### Step 1: Clone the Repository
```bash
git clone https://github.com/Sujan13-2004/NovaRAG-Research-Studio.git
cd NovaRAG-Research-Studio
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### Step 5: Build the Research Corpus (Optional)
```bash
# Download 100+ research papers from arXiv
python download_papers.py

# Ingest papers into the ChromaDB vector store
python resume_ingest.py
```

---

## ⚙️ Setup Instructions

### Database Initialization
The ChromaDB vector store is automatically initialized when the application starts. If starting fresh:

1. Delete the `chroma_db/` directory (if it exists)
2. Upload PDFs through the **Upload & Corpus** page, or
3. Run `python download_papers.py` to auto-populate the corpus

### First-Time Model Downloads
On the first run, two small models will be automatically downloaded:
- **all-MiniLM-L6-v2** (~80MB) — Sentence embedding model
- **ms-marco-MiniLM-L-6-v2** (~25MB) — FlashRank reranker model

These are cached locally after the first download.

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key for LLM generation |

The API key can also be entered through the **Settings** page in the UI if not configured via `.env`.

---

## ▶️ Running the Project

### Development Server
```bash
streamlit run app.py
```
The application will launch at `http://localhost:8501`.

### With Custom Port
```bash
streamlit run app.py --server.port 8080
```

### With Wide Layout (Default)
The app is pre-configured with `layout="wide"` and an expanded sidebar.

---

## 📡 API Endpoints

NovaRAG is a Streamlit application and does not expose traditional REST API endpoints. Instead, it provides **internal Python APIs** consumed by the UI:

### Core Pipeline Functions

| Function | Module | Description |
|----------|--------|-------------|
| `run_rag_query()` | `rag_pipeline.py` | Main RAG pipeline: retrieve → rerank → generate |
| `add_pdf_to_vector_store()` | `ingest.py` | Ingest a PDF into ChromaDB |
| `delete_document()` | `ingest.py` | Remove a document from the vector store |
| `list_documents()` | `ingest.py` | List all indexed documents with metadata |
| `check_input_guardrail()` | `guardrails.py` | Validate user input for safety |
| `check_output_guardrail()` | `guardrails.py` | Score generated output for groundedness |
| `validate_citations()` | `guardrails.py` | Verify citation markers map to sources |
| `classify_intent()` | `intent_classifier.py` | Classify query into one of 4 intents |
| `generate_pdf_report()` | `pdf_generator.py` | Generate a professional PDF research brief |

### RAG Pipeline Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `top_k_retrieve` | 20 | 5–50 | Initial candidate retrieval count |
| `top_n_rerank` | 7 | 3–20 | Final reranked context count |
| `max_chunks_per_doc` | 3 | 1–10 | Max chunks per unique document |
| `groundedness_threshold` | 0.55 | 0.0–1.0 | Hallucination warning threshold |

---

## 👤 User Workflow

```
1. Launch Application
   └── Premium animated landing page with feature showcase

2. Enter NovaRAG
   └── Sequential loading gateway with progress bar

3. Dashboard
   ├── View corpus statistics (papers, pages, chunks, queries)
   ├── Inspect category distribution (donut chart)
   ├── Review publication timeline (area chart)
   └── Quick-action navigation cards

4. Upload Papers
   ├── Drag & drop PDF files
   ├── Automatic text extraction & chunking
   ├── ChromaDB indexing with progress tracking
   └── Category auto-classification

5. Research Query
   ├── Select scope (full corpus or specific paper)
   ├── Enter natural language query
   ├── Automatic intent classification
   ├── Input guardrail validation
   ├── RAG pipeline execution
   ├── Output groundedness scoring
   ├── Citation validation
   ├── Results display (intent-aware rendering)
   └── PDF report download

6. Evidence Extraction
   ├── Select target document
   ├── Enter extraction query
   ├── View extracted facts with confidence scores
   ├── Inspect supporting quotes & page numbers
   └── Evidence matrix summary

7. Analytics
   ├── Query history timeline
   ├── Groundedness score trends
   ├── Success rate tracking
   └── Category-level analytics
```

---

## 🔮 Future Enhancements

- [ ] **Multi-modal RAG** — Support for images, tables, and figures within papers
- [ ] **Collaborative Workspaces** — Multi-user annotation and shared collections
- [ ] **Fine-tuned Domain Models** — Custom embedding models trained on domain-specific corpora
- [ ] **Knowledge Graph Integration** — Entity-relationship extraction across papers
- [ ] **Streaming Responses** — Real-time token streaming for faster perceived latency
- [ ] **Export to LaTeX/Word** — Extended report format support
- [ ] **API Server Mode** — RESTful endpoints via FastAPI for programmatic access
- [ ] **Batch Processing** — Scheduled corpus updates and automated synthesis reports
- [ ] **User Authentication** — Role-based access control for enterprise deployments
- [ ] **Prompt Template Library** — Customizable system prompts for different research domains

---

## 📸 Screenshots

> Screenshots of the application can be added here. The application features:
> - 🎨 **Landing Page** — Dark-themed entrance with animated particles, typing effects, and feature cards
> - 📊 **Dashboard** — Metric cards, donut charts, area charts, and quick actions
> - 🔍 **Research Assistant** — Query interface with scope selector, intent badges, guardrail audits, and synthesis output
> - 📤 **Upload & Corpus** — File uploader with progress tracking and indexed document list
> - 📚 **Browse Papers** — Filterable paper browser with category badges
> - 🔎 **Evidence Extraction** — Fact extraction with confidence scores and supporting quotes
> - 🛡️ **Safety Audit** — Guardrail testing interface
> - ⚙️ **Settings** — API configuration, model info, and pipeline parameter tuning

---

## 📝 Conclusion

NovaRAG Research Studio represents a comprehensive implementation of a production-grade RAG system designed specifically for academic research analysis. By combining local embedding models, cross-encoder reranking, intent-aware query classification, multi-tier hallucination detection, and professional report generation, it provides researchers with a reliable, transparent, and verifiable AI-assisted literature review tool.

The system prioritizes **groundedness** and **citation integrity** over raw generative capabilities, ensuring that every claim in a generated synthesis can be traced back to specific passages in the source material. This design philosophy makes NovaRAG suitable for academic settings where factual accuracy and intellectual honesty are paramount.

---

<p align="center">
  <strong>NovaRAG Research Studio v2.0.0</strong><br/>
  <em>AI Research Paper Summarizer & Report Generator</em><br/>
  Built with ❤️ using Python, Streamlit, ChromaDB, and Google Gemini
</p>
]]>
