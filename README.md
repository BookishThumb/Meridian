# Meridian — Enterprise Knowledge Assistant 🌐

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![Gradio](https://img.shields.io/badge/Gradio-Frontend-orange)
![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-success)

</p>

An **Enterprise Knowledge Assistant** built using **Retrieval-Augmented Generation (RAG)** that enables employees to query corporate documents using natural language.

Meridian combines **semantic vector search**, **BM25 lexical retrieval**, and **Large Language Models (LLMs)** to generate accurate, source-grounded answers with confidence scoring and hallucination safeguards.

---



# ✨ Features

* Hybrid Retrieval (Semantic + BM25)
* Enterprise PDF Knowledge Base
* Natural Language Question Answering
* Query Rewriting for Better Retrieval
* Source Citations
* Confidence Score
* Hallucination Detection
* FastAPI REST API
* Gradio Chat Interface
* Automated Evaluation Pipeline

---

# 📁 Project Structure

```text
enterprise-knowledge-assistant/
│
├── app/
│   ├── main.py
│   ├── rag_pipeline.py
│   ├── retriever.py
│   ├── llm.py
│   ├── query_rewriter.py
│   ├── evaluator.py
│   └── logger.py
│
├── ui/
│   └── gradio_app.py
│
├── scripts/
│   └── generate_docs.py
│
├── data/
│
├── requirements.txt
├── .env.example
└── README.md
```

---

# 🚀 Getting Started

## Prerequisites

* Python 3.11+
* Groq API Key

Create your API key from:

https://console.groq.com/

---

# Installation

Clone the repository:

```bash
git clone https://github.com/BookishThumb/Meridian

cd enterprise-knowledge-assistant
```

Create a virtual environment.

### Windows

```bash
python -m venv .venv

.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv

source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Copy the example environment file.

```bash
cp .env.example .env
```

Add your Groq API key.

```env
GROQ_API_KEY=gsk_your_api_key_here
```

---

# Running the Project

## Step 1 — Generate Sample Documents

This creates sample enterprise policy PDFs.

```bash
python scripts/generate_docs.py
```

---

## Step 2 — Start FastAPI Backend

```bash
uvicorn app.main:app --reload
```

Backend:

```
http://127.0.0.1:8000
```

Swagger API Documentation:

```
http://127.0.0.1:8000/docs
```

---

## Step 3 — Launch Gradio UI

Open another terminal.

```bash
python ui/gradio_app.py
```

Open:

```
http://127.0.0.1:7860
```

---

# 🏗 System Architecture

```text
                    +----------------------+
                    |     Gradio UI        |
                    +----------+-----------+
                               |
                               |
                               v
                    +----------------------+
                    |      FastAPI API     |
                    +----------+-----------+
                               |
                               |
                               v
                    +----------------------+
                    |     RAG Pipeline      |
                    +----------+-----------+
                               |
        +----------------------+----------------------+
        |                                             |
        v                                             v

+--------------------+                    +----------------------+
| Query Rewriter     |                    | Hybrid Retriever     |
| GPT-OSS-20B        |                    | Semantic + BM25       |
+--------------------+                    +----------+-----------+
                                                     |
                    +--------------------------------+
                    |
          +---------+---------+
          |                   |
          v                   v

    ChromaDB            BM25 Retriever

          +-------------------+
                    |
                    v

          Candidate Fusion

      (0.6 Semantic + 0.4 BM25)

                    |
                    v

          Top Retrieved Chunks

                    |
                    v

          Groq Llama 3.3-70B

                    |
                    v

          Final Response
```

---

# ⚙ Technology Stack

| Component       | Technology                             |
| --------------- | -------------------------------------- |
| Backend         | FastAPI                                |
| Frontend        | Gradio                                 |
| Vector Database | ChromaDB                               |
| Embeddings      | sentence-transformers/all-MiniLM-L6-v2 |
| Lexical Search  | rank_bm25                              |
| Generator LLM   | Groq Llama 3.3-70B Versatile           |
| Query Rewriter  | openai/gpt-oss-20b                     |

---

# 🧠 Design Decisions

## Hybrid Retrieval

Pure semantic search struggles with:

* Policy IDs
* Employee codes
* Acronyms
* Exact terminology

To overcome this, Meridian combines:

```
Final Score

=

0.6 × Semantic Similarity

+

0.4 × BM25 Score
```

This improves retrieval quality while preserving semantic understanding.

---

## BM25 Index Caching

Instead of rebuilding the BM25 index for every query, the index is cached immediately after ingestion.

Benefits:

* Lower latency
* Faster repeated searches
* Reduced CPU usage

---

## Query Rewriting

User questions are rewritten before retrieval to improve search quality.

Example:

**User**

> What about leave policy?

↓

**Rewritten**

> Explain the company's employee leave policy and annual leave guidelines.

---

## Hallucination Prevention

If relevant information is unavailable, the assistant responds with:

* Low Confidence
* No supporting citations
* Safe "Information Not Found" response

instead of generating fabricated answers.

---

# 📊 Evaluation

Run:

```bash
python app/evaluator.py
```

The evaluation suite measures:

## 1. Source Citation Accuracy

Checks whether the generated response references the correct document and section.

---

## 2. Keyword Relevance

Measures overlap between expected keywords and generated answers.

---

## 3. Hallucination Rate

Injects unrelated questions such as:

> "How do I cook pasta?"

The expected behavior is:

* Low Confidence
* No citations
* Information Not Found

---

# 📈 Retrieval Pipeline

```
User Query

↓

Query Rewriting

↓

Generate Embedding

↓

Semantic Search (ChromaDB)

+

BM25 Search

↓

Candidate Fusion

↓

Top-K Context

↓

LLM Generation

↓

Grounded Answer
```

---

# 🔒 Security

* Environment variables for API keys
* SHA-256 password hashing
* Centralized logging
* Input validation using Pydantic
* Citation-based grounding to reduce hallucinations

---

# ⚠ Current Limitations

* BM25 is stored in memory and is not distributed.
* PDF parsing is limited to text extraction.
* Session memory is process-local.
* No OCR support for scanned PDFs.
* No authentication or role-based access control.

---

# 🚀 Future Improvements

* Elasticsearch integration for scalable lexical search
* OCR support for scanned documents
* Vision-Language models for charts and tables
* Redis-backed distributed session storage
* Agentic workflows with SQL and enterprise tools
* User authentication and RBAC
* Streaming LLM responses
* Docker and Kubernetes deployment
* CI/CD pipeline with GitHub Actions



---

# 👨‍💻 Author

Rounak Banerjee

