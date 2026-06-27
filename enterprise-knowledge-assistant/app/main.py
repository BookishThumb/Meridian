import os
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from app.rag_pipeline import RAGPipeline
import gradio as gr
from ui.gradio_app import demo

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize FastAPI App
app = FastAPI(
    title="Meridian — Enterprise Knowledge Assistant API",
    description="Backend API for AnthraSync Technologies' RAG system.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session history storage (In-memory dict mapping session_id -> list of chat messages)
# Message structure: {"role": "user"|"assistant", "content": "str"}
session_memories: Dict[str, List[Dict[str, str]]] = {}

# Initialize pipeline lazily
pipeline = None

def get_pipeline():
    global pipeline
    if pipeline is None:
        try:
            pipeline = RAGPipeline()
        except Exception as e:
            logger.error(f"Failed to initialize RAG Pipeline: {e}")
            raise HTTPException(status_code=500, detail=f"Pipeline initialization error: {str(e)}")
    return pipeline

# Pydantic Schemas
class AskRequest(BaseModel):
    question: str = Field(..., description="The user's search query or question.")
    session_id: str = Field(default="default_session", description="Unique session identifier for conversation history.")

class SourceInfo(BaseModel):
    document: str
    page: int
    section: str
    text: str

class AskResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    confidence: float
    confidence_label: str
    rewritten_query: str

class IngestResponse(BaseModel):
    status: str
    chunks_indexed: int

class HealthResponse(BaseModel):
    status: str
    database_connected: bool

class DocumentItem(BaseModel):
    document: str
    chunks: int

# Endpoints
@app.get("/health", response_model=HealthResponse)
def get_health():
    """Returns the API and database connection health status."""
    try:
        pipe = get_pipeline()
        # Ping database by calling a simple inspect count
        pipe.get_documents()
        return {"status": "healthy", "database_connected": True}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database_connected": False}

@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """Processes user query, rewrites it using session context, retrieves sources, and returns answer."""
    question = request.question.strip()
    session_id = request.session_id
    
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    pipe = get_pipeline()
    
    # 1. Retrieve session history (up to last 5 turns / 10 messages)
    history = session_memories.get(session_id, [])
    
    # 2. Invoke RAG pipeline
    logger.info(f"Session {session_id} - Processing question: '{question}'")
    result = pipe.ask(question, history)
    
    # 3. Update session history if request is successful and answer is found
    if result["confidence_label"] != "Low":
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": result["answer"]})
        # Keep only the last 10 messages (5 turns)
        session_memories[session_id] = history[-10:]
        
    return result

@app.post("/ingest", response_model=IngestResponse)
def trigger_ingestion():
    """Triggers clean document parsing, chunking, and embedding generation."""
    pipe = get_pipeline()
    try:
        chunks_count = pipe.ingest()
        return {"status": "success", "chunks_indexed": chunks_count}
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion process failed: {str(e)}")

@app.get("/documents", response_model=List[DocumentItem])
def get_documents_list():
    """Returns a list of all indexed files and their respective chunk counts."""
    pipe = get_pipeline()
    try:
        doc_counts = pipe.get_documents()
        return [{"document": doc, "chunks": count} for doc, count in doc_counts.items()]
    except Exception as e:
        logger.error(f"Failed to fetch document counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/clear/{session_id}")
def clear_session_memory(session_id: str):
    """Clears conversation history for the specified session ID."""
    if session_id in session_memories:
        del session_memories[session_id]
        logger.info(f"Cleared session history for: {session_id}")
    return {"status": "success", "message": f"Session {session_id} history cleared."}

# Mount Gradio UI
app = gr.mount_gradio_app(app, demo, path="/")
