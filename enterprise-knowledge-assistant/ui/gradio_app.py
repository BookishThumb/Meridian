import os
import uuid
import logging
import requests
import gradio as gr
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# API Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", 8000))
API_URL = f"http://{API_HOST}:{API_PORT}"

# Custom CSS for modern premium SaaS aesthetics
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg-main: #0f0f1a;
    --bg-card: #1e1e2e;
    --border-card: #2a2a3e;
    --text-main: #e2e8f0;
    --accent-indigo: #6366f1;
    --accent-purple: #8b5cf6;
}

body, .gradio-container {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    background-color: var(--bg-main) !important;
    color: var(--text-main) !important;
}

/* 1. HEADER */
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.meridian-header {
    background: linear-gradient(-45deg, #0f172a, #312e81, #4c1d95, #0f0f1a);
    background-size: 300% 300%;
    animation: gradientShift 15s ease infinite;
    color: white;
    padding: 32px;
    border-radius: 16px;
    margin-bottom: 24px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    display: flex;
    flex-direction: column;
}

.meridian-title-container {
    display: flex;
    align-items: center;
    gap: 12px;
}

.meridian-title {
    font-size: 36px !important;
    font-weight: 800 !important;
    margin: 0 !important;
    color: #FFFFFF !important;
    letter-spacing: -0.5px;
}

.meridian-subtitle {
    font-size: 15px !important;
    font-weight: 500;
    opacity: 0.8;
    margin: 8px 0 0 0 !important;
    color: #C7D2FE !important;
}

/* 2. SIDEBAR */
.brand-sidebar {
    background: var(--bg-card) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    border: 1px solid var(--border-card) !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
}

.doc-card {
    background-color: var(--bg-main);
    border: 1px solid var(--border-card);
    border-left: 3px solid var(--accent-indigo);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.doc-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.doc-name {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-main);
    display: flex;
    align-items: center;
    gap: 8px;
}

.doc-pill {
    background-color: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 8px;
    border-radius: 9999px;
    border: 1px solid rgba(99, 102, 241, 0.3);
}

/* Buttons */
button.primary-btn {
    background: linear-gradient(135deg, var(--accent-indigo) 0%, var(--accent-purple) 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: opacity 0.2s ease, transform 0.1s ease !important;
}
button.primary-btn:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

button.outline-red-btn {
    background: transparent !important;
    border: 1px solid #ef4444 !important;
    color: #ef4444 !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
button.outline-red-btn:hover {
    background: rgba(239, 68, 68, 0.1) !important;
}

/* 3. CHAT AREA */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.message {
    animation: fadeIn 0.4s ease forwards;
}

/* Override Gradio Chatbot Layout */
.message-row {
    margin-bottom: 24px !important;
}

.user-row .message {
    background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
    border: none !important;
    color: white !important;
    border-radius: 16px 16px 2px 16px !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
}

.bot-row .message {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-card) !important;
    color: var(--text-main) !important;
    border-radius: 16px 16px 16px 2px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    position: relative;
    padding-left: 20px !important;
}

.bot-row .avatar-container img {
    border-radius: 8px !important;
}

/* 6. INPUT BAR */
.pill-input textarea {
    border-radius: 9999px !important;
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-card) !important;
    color: var(--text-main) !important;
    padding: 14px 24px !important;
    transition: all 0.3s ease !important;
}

.pill-input textarea:focus {
    border-color: var(--accent-indigo) !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3), 0 0 15px rgba(99, 102, 241, 0.1) !important;
    outline: none !important;
}

/* Source Cards styling */
.source-card {
    background-color: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 12px;
}
.source-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}
.source-card-title {
    font-weight: 600;
    color: var(--text-main);
    font-size: 13px;
}
.source-card-subtitle {
    font-size: 11px;
    color: #94a3b8;
}
.source-card-text {
    font-size: 12px;
    color: #cbd5e1;
    font-style: italic;
    border-left: 2px solid var(--accent-purple);
    padding-left: 10px;
    margin-top: 8px;
}
"""

def get_documents_html():
    """Queries FastAPI /documents endpoint and returns styled HTML cards."""
    try:
        response = requests.get(f"{API_URL}/documents")
        if response.status_code == 200:
            docs = response.json()
            if not docs:
                return "<p style='color: #94A3B8; font-style: italic; font-size: 13px;'>No documents indexed yet.</p>"
                
            html = "<div>"
            for doc in docs:
                name = doc["document"]
                chunks = doc["chunks"]
                html += f'''
                <div class="doc-card">
                    <div class="doc-name">📄 <span>{name}</span></div>
                    <div class="doc-pill">{chunks} chunks</div>
                </div>
                '''
            html += "</div>"
            return html
        else:
            return f"<p style='color: #F87171;'>Failed to load documents ({response.status_code})</p>"
    except Exception as e:
        return f"<p style='color: #F87171; font-size: 12px;'>API Offline (Run FastAPI backend first)</p>"

def trigger_ingest():
    """Triggers document ingestion and returns updated document status."""
    try:
        response = requests.post(f"{API_URL}/ingest")
        if response.status_code == 200:
            data = response.json()
            chunks = data["chunks_indexed"]
            gr.Info(f"Ingestion successful! {chunks} chunks indexed.")
            return get_documents_html()
        else:
            gr.Warning(f"Ingestion failed: {response.text}")
            return get_documents_html()
    except Exception as e:
        gr.Error(f"Connection error: {e}")
        return get_documents_html()

def clear_session(session_id):
    """Sends session clear command to FastAPI backend."""
    try:
        requests.post(f"{API_URL}/session/clear/{session_id}")
    except Exception as e:
        logger.error(f"Failed to clear session on backend: {e}")
    return [], str(uuid.uuid4())

def format_chat_response(answer: str, sources: list, confidence_label: str, confidence_score: float) -> str:
    """Formats the LLM response with styled HTML confidence badges and source cards."""
    # Confidence Badge styling
    if confidence_label == "High":
        bg_color, text_color, border_color, icon = "rgba(16, 185, 129, 0.15)", "#10B981", "rgba(16, 185, 129, 0.3)", "✅"
    elif confidence_label == "Medium":
        bg_color, text_color, border_color, icon = "rgba(245, 158, 11, 0.15)", "#F59E0B", "rgba(245, 158, 11, 0.3)", "⚠️"
    else:
        bg_color, text_color, border_color, icon = "rgba(239, 68, 68, 0.15)", "#EF4444", "rgba(239, 68, 68, 0.3)", "❌"
        
    badge_html = f'''
    <div style="display: flex; align-items: center; gap: 6px; padding: 6px 16px; border-radius: 9999px; font-size: 13px; font-weight: 600; background-color: {bg_color}; color: {text_color}; border: 1px solid {border_color}; width: fit-content; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
        <span>{icon}</span>
        <span>Confidence: {confidence_label}</span>
        <span style="opacity: 0.7; font-size: 11px; margin-left: 4px;">({confidence_score:.2f})</span>
    </div>
    <hr style="border: 0; border-top: 1px solid #2a2a3e; margin: 16px 0;" />
    '''
    
    sources_html = ""
    if sources:
        sources_html += f'<details style="margin-top: 20px; border: 1px solid #2a2a3e; border-radius: 8px; padding: 12px 16px; background-color: #0f0f1a;">'
        sources_html += f'<summary style="font-size: 13px; cursor: pointer; color: #8b5cf6; font-weight: 600; list-style: none; display: flex; align-items: center;">View Sources ({len(sources)})</summary>'
        sources_html += f'<div style="margin-top: 16px; max-height: 300px; overflow-y: auto; padding-right: 4px;">'
        for idx, src in enumerate(sources):
            doc = src["document"]
            page = src["page"]
            section = src["section"]
            text = src["text"]
            sources_html += f'''
            <div class="source-card">
                <div class="source-card-header">
                    <span>📄</span>
                    <span class="source-card-title">{doc}</span>
                </div>
                <div class="source-card-subtitle">Page {page} • Section: {section}</div>
                <div class="source-card-text">"{text}"</div>
            </div>
            '''
        sources_html += f'</div></details>'
        
    return f"{badge_html}\n\n{answer}\n\n{sources_html}"

def respond(message, chat_history, session_id):
    """Processes user message, updates chatbot list, and queries API."""
    if not message.strip():
        return "", chat_history
        
    chat_history = chat_history or []
    
    try:
        response = requests.post(
            f"{API_URL}/ask",
            json={"question": message, "session_id": session_id}
        )
        if response.status_code == 200:
            data = response.json()
            answer = data["answer"]
            sources = data["sources"]
            confidence_label = data["confidence_label"]
            confidence = data["confidence"]
            
            formatted_ans = format_chat_response(answer, sources, confidence_label, confidence)
            chat_history.append((message, formatted_ans))
        else:
            chat_history.append((message, f"❌ Error: API server returned {response.status_code} ({response.text})"))
    except Exception as e:
        chat_history.append((message, f"❌ Error: Could not connect to API server. Please ensure the backend is running.\\n({e})"))
        
    return "", chat_history

# Create SVG avatar (Meridian "M")
avatar_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100"><rect width="100" height="100" rx="20" fill="#1e1e2e"/><path d="M 25 75 L 25 35 L 50 60 L 75 35 L 75 75" stroke="#6366f1" stroke-width="12" fill="none" stroke-linejoin="round" stroke-linecap="round"/></svg>"""
import tempfile
avatar_path = os.path.join(tempfile.gettempdir(), "meridian_avatar.svg")
with open(avatar_path, "w") as f:
    f.write(avatar_svg)

# SVG compass icon for header
compass_svg = """
<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"></circle>
  <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
</svg>
"""

# Gradio Page Layout Construction
with gr.Blocks(title="Meridian — Enterprise Knowledge Assistant", css=custom_css, theme=gr.themes.Base()) as demo:
    # State tracking
    session_id_state = gr.State(lambda: str(uuid.uuid4()))
    
    # Title Banner
    with gr.Row(elem_classes=["meridian-header"]):
        with gr.Column():
            gr.HTML(f"""
            <div class='meridian-title-container'>
                {compass_svg}
                <h1 class='meridian-title'>Meridian</h1>
            </div>
            <p class='meridian-subtitle'>Enterprise Knowledge, Instantly Answered</p>
            """)
            
    # Main Dashboard Columns
    with gr.Row():
        # Sidebar Control Column
        with gr.Column(scale=1, min_width=280, elem_classes=["brand-sidebar"]):
            gr.Markdown("### 🏢 AnthraSync Directory")
            gr.Markdown("Click **Index Documents** below to scan the source directory (`data/documents/`) and generate vector embeddings.")
            
            # Document Listing Table
            document_list_html = gr.HTML(value=get_documents_html(), label="Indexed Documents")
            
            # Ingestion & Sync Controls
            ingest_btn = gr.Button("⚡ Index Documents", elem_classes=["primary-btn"])
            clear_btn = gr.Button("🗑️ Clear Chat", elem_classes=["outline-red-btn"])
            
            gr.Markdown("---")
            gr.Markdown("#### System Specs")
            gr.Markdown("- **Embeddings:** `all-MiniLM-L6-v2`\\n- **Vector Store:** ChromaDB\\n- **LLM:** Groq Llama 3.3")
            
        # Chatbot Window Column
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Meridian Chat Console",
                bubble_full_width=False,
                height=550,
                render_markdown=True,
                avatar_images=(None, avatar_path)
            )
            
            with gr.Row():
                txt_input = gr.Textbox(
                    show_label=False,
                    placeholder="Ask a question about HR policies, FAQs, product features...",
                    scale=4,
                    container=False,
                    elem_classes=["pill-input"]
                )
                submit_btn = gr.Button("Send ➔", elem_classes=["primary-btn"], scale=1)
                
    # Event Handlers Bindings
    # Ingestion Click
    ingest_btn.click(
        fn=trigger_ingest,
        outputs=[document_list_html]
    )
    
    # Clear Session Memory
    clear_btn.click(
        fn=clear_session,
        inputs=[session_id_state],
        outputs=[chatbot, session_id_state]
    )
    
    # Message Submit Action
    submit_event = submit_btn.click(
        fn=respond,
        inputs=[txt_input, chatbot, session_id_state],
        outputs=[txt_input, chatbot]
    )
    
    txt_input.submit(
        fn=respond,
        inputs=[txt_input, chatbot, session_id_state],
        outputs=[txt_input, chatbot]
    )
    
    # Update documents list on startup
    demo.load(fn=get_documents_html, outputs=[document_list_html])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
