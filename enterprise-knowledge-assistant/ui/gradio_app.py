import os
import logging
import requests
import gradio as gr
from dotenv import load_dotenv

import auth
import chat_history as ch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", 8000)))
API_URL = f"http://{API_HOST}:{API_PORT}"

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

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.hero-title {
    font-size: 64px !important;
    font-weight: 800 !important;
    text-align: center;
    background: linear-gradient(-45deg, #a5b4fc, #6366f1, #8b5cf6, #c4b5fd);
    background-size: 300% 300%;
    animation: gradientShift 5s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px !important;
}

.hero-tagline {
    font-size: 24px !important;
    text-align: center;
    font-weight: 600;
    color: white;
    margin-bottom: 16px !important;
}

.hero-subtext {
    font-size: 16px !important;
    text-align: center;
    color: #94a3b8;
    max-width: 600px;
    margin: 0 auto 32px auto !important;
}

.glow-card {
    background-color: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    transition: all 0.3s ease;
    height: 100%;
}
.glow-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.3);
    border-color: var(--accent-indigo);
}

.auth-card {
    background-color: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 16px;
    padding: 40px;
    max-width: 400px;
    margin: 60px auto;
    box-shadow: 0 20px 40px rgba(0,0,0,0.5);
}

.meridian-header {
    background: linear-gradient(-45deg, #0f172a, #312e81, #4c1d95, #0f0f1a);
    background-size: 300% 300%;
    animation: gradientShift 15s ease infinite;
    color: white;
    padding: 24px 32px;
    border-radius: 16px;
    margin-bottom: 24px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.meridian-title-container {
    display: flex;
    align-items: center;
    gap: 12px;
}
.meridian-title {
    font-size: 32px !important;
    font-weight: 800 !important;
    margin: 0 !important;
    color: #FFFFFF !important;
}

.brand-sidebar {
    background: var(--bg-card) !important;
    border-radius: 16px !important;
    padding: 16px !important;
    border: 1px solid var(--border-card) !important;
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
}

button.primary-btn {
    background: linear-gradient(135deg, var(--accent-indigo) 0%, var(--accent-purple) 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
button.primary-btn:hover {
    box-shadow: 0 0 15px rgba(99, 102, 241, 0.5) !important;
    transform: translateY(-1px);
}
button.outline-red-btn {
    background: transparent !important;
    border: 1px solid #ef4444 !important;
    color: #ef4444 !important;
    border-radius: 8px !important;
    max-width: 100px !important;
}
button.outline-red-btn:hover {
    background: rgba(239, 68, 68, 0.1) !important;
}

.user-row .message {
    background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
    border: none !important;
    color: white !important;
    border-radius: 16px 16px 2px 16px !important;
}
.bot-row .message {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-card) !important;
    color: var(--text-main) !important;
    border-radius: 16px 16px 16px 2px !important;
    padding-left: 20px !important;
}
.bot-row .avatar-container img { border-radius: 8px !important; }

.pill-input textarea {
    border-radius: 9999px !important;
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-card) !important;
    color: var(--text-main) !important;
    padding: 14px 24px !important;
}
.pill-input textarea:focus {
    border-color: var(--accent-indigo) !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3) !important;
}

.user-badge {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(255,255,255,0.1);
    padding: 6px 16px;
    border-radius: 9999px;
    border: 1px solid rgba(255,255,255,0.2);
    width: fit-content;
}
.user-badge-container {
    max-width: 150px !important;
    display: flex;
    align-items: center;
    justify-content: flex-end;
}
.avatar-circle {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-indigo), var(--accent-purple));
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}
.session-item {
    padding: 12px;
    border: 1px solid var(--border-card);
    border-radius: 8px;
    margin-bottom: 8px;
    cursor: pointer;
    background: var(--bg-main);
}
.session-item:hover {
    border-color: var(--accent-indigo);
}
.session-active {
    border-left: 3px solid var(--accent-indigo);
    background: rgba(99, 102, 241, 0.1);
}
"""

avatar_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100"><rect width="100" height="100" rx="20" fill="#1e1e2e"/><path d="M 25 75 L 25 35 L 50 60 L 75 35 L 75 75" stroke="#6366f1" stroke-width="12" fill="none" stroke-linejoin="round" stroke-linecap="round"/></svg>"""
import tempfile
avatar_path = os.path.join(tempfile.gettempdir(), "meridian_avatar.svg")
with open(avatar_path, "w") as f: f.write(avatar_svg)

compass_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon></svg>"""

def get_documents_html():
    try:
        response = requests.get(f"{API_URL}/documents")
        if response.status_code == 200:
            docs = response.json()
            if not docs: return "<p style='color: #94A3B8; font-style: italic; font-size: 13px;'>No documents indexed yet.</p>"
            html = "<div>"
            for doc in docs:
                html += f'<div class="doc-card"><div class="doc-name">📄 <span>{doc["document"]}</span></div><div style="background-color: rgba(99, 102, 241, 0.15); color: #a5b4fc; font-size: 11px; font-weight: 700; padding: 4px 8px; border-radius: 9999px; border: 1px solid rgba(99, 102, 241, 0.3);">{doc["chunks"]} chunks</div></div>'
            html += "</div>"
            return html
        return "<p style='color: #F87171;'>Failed to load documents</p>"
    except:
        return "<p style='color: #F87171; font-size: 12px;'>API Offline</p>"

def trigger_ingest():
    try:
        response = requests.post(f"{API_URL}/ingest")
        if response.status_code == 200:
            gr.Info(f"Ingestion successful! {response.json()['chunks_indexed']} chunks indexed.")
        else:
            gr.Warning(f"Ingestion failed: {response.text}")
    except Exception as e:
        gr.Error(f"Connection error: {e}")
    return get_documents_html()

def format_chat_response(answer: str, sources: list, confidence_label: str, confidence_score: float) -> str:
    if confidence_label == "High": bg, txt, border, icon = "rgba(16, 185, 129, 0.15)", "#10B981", "rgba(16, 185, 129, 0.3)", "✅"
    elif confidence_label == "Medium": bg, txt, border, icon = "rgba(245, 158, 11, 0.15)", "#F59E0B", "rgba(245, 158, 11, 0.3)", "⚠️"
    else: bg, txt, border, icon = "rgba(239, 68, 68, 0.15)", "#EF4444", "rgba(239, 68, 68, 0.3)", "❌"
    badge_html = f'<div style="display: flex; align-items: center; gap: 6px; padding: 6px 16px; border-radius: 9999px; font-size: 13px; font-weight: 600; background-color: {bg}; color: {txt}; border: 1px solid {border}; width: fit-content;"><span>{icon}</span><span>Confidence: {confidence_label}</span><span style="opacity: 0.7; font-size: 11px; margin-left: 4px;">({confidence_score:.2f})</span></div><hr style="border: 0; border-top: 1px solid #2a2a3e; margin: 16px 0;" />'
    
    sources_html = ""
    if sources:
        sources_html += f'<details style="margin-top: 20px; border: 1px solid #2a2a3e; border-radius: 8px; padding: 12px 16px; background-color: #0f0f1a;"><summary style="font-size: 13px; cursor: pointer; color: #8b5cf6; font-weight: 600; list-style: none;">View Sources ({len(sources)})</summary><div style="margin-top: 16px; max-height: 300px; overflow-y: auto;">'
        for src in sources:
            sources_html += f'<div style="background-color: var(--bg-card); border: 1px solid var(--border-card); border-radius: 8px; padding: 12px 16px; margin-bottom: 12px;"><div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;"><span>📄</span><span style="font-weight: 600; color: var(--text-main); font-size: 13px;">{src["document"]}</span></div><div style="font-size: 11px; color: #94a3b8;">Page {src["page"]} • Section: {src["section"]}</div><div style="font-size: 12px; color: #cbd5e1; font-style: italic; border-left: 2px solid var(--accent-purple); padding-left: 10px; margin-top: 8px;">"{src["text"]}"</div></div>'
        sources_html += f'</div></details>'
    return f"{badge_html}\n\n{answer}\n\n{sources_html}"

def handle_login(username, password):
    if auth.authenticate(username, password):
        sid = ch.create_new_session(username)
        badge = f"<div class='user-badge'><div class='avatar-circle'>{username[0].upper()}</div><span style='color:white; font-weight:600;'>{username}</span></div>"
        return gr.update(visible=False), gr.update(visible=True), badge, "", "", username, sid, False, []
    else:
        return gr.update(visible=True), gr.update(visible=False), "", "❌ Invalid username or password", "", None, None, False, []

def handle_logout():
    return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), "", "", None, None, []

def start_new_session(username):
    if not username: return None, [], False
    sid = ch.create_new_session(username)
    return sid, [], False

def load_session(username, session_id):
    msgs = ch.get_session_messages(username, session_id)
    chat_format = []
    for m in msgs:
        if m["role"] == "user":
            chat_format.append((m["content"], None))
        else:
            ans = m["content"]
            if "sources" in m:
                ans = format_chat_response(m["content"], m["sources"], m.get("confidence_label", "High"), m.get("confidence", 1.0))
            if chat_format and chat_format[-1][1] is None:
                chat_format[-1] = (chat_format[-1][0], ans)
            else:
                chat_format.append((None, ans))
    return session_id, chat_format, True

def handle_message(message, chat_history, username, session_id, read_only):
    if not message.strip(): 
        yield "", chat_history
        return
    if read_only:
        gr.Warning("You are viewing a past session. Start a New Chat to ask questions.")
        yield "", chat_history
        return
        
    chat_history = chat_history or []
    
    # Save user message
    ch.save_message(username, session_id, "user", message)
    chat_history.append((message, None))
    yield "", chat_history
    
    try:
        response = requests.post(f"{API_URL}/ask", json={"question": message, "session_id": session_id})
        if response.status_code == 200:
            data = response.json()
            answer = data["answer"]
            sources = data["sources"]
            conf_label = data["confidence_label"]
            conf = data["confidence"]
            
            # Save assistant message
            ch.save_message(username, session_id, "assistant", answer, sources=sources, confidence=conf)
            
            formatted_ans = format_chat_response(answer, sources, conf_label, conf)
            chat_history[-1] = (message, formatted_ans)
        else:
            chat_history[-1] = (message, f"❌ API Error: {response.status_code}")
    except Exception as e:
        chat_history[-1] = (message, f"❌ Connection Error: {e}")
        
    yield "", chat_history

with gr.Blocks(title="Meridian", css=custom_css, theme=gr.themes.Base()) as demo:
    username_state = gr.State(None)
    session_id_state = gr.State(None)
    read_only_state = gr.State(False)
    
    # === LANDING PAGE ===
    with gr.Column(visible=True) as landing_col:
        gr.HTML(f"<div style='padding: 60px 0;'><h1 class='hero-title'>Meridian</h1><p class='hero-tagline'>Enterprise Knowledge, Instantly Answered</p><p class='hero-subtext'>Ask questions across all your internal documents and get accurate, cited answers in seconds.</p></div>")
        
        with gr.Row():
            gr.HTML("<div></div>")
            get_started_btn = gr.Button("Get Started →", elem_classes=["primary-btn"], scale=2)
            learn_more_btn = gr.Button("Learn More ↓", scale=2)
            gr.HTML("<div></div>")
            
        gr.HTML("<div style='height: 40px;'></div>")
        
        with gr.Row():
            with gr.Column(elem_classes=["glow-card"]):
                gr.HTML("<h2>🔍 Semantic Search</h2><p style='color:#94a3b8;'>Finds relevant information even when exact keywords don't match</p>")
            with gr.Column(elem_classes=["glow-card"]):
                gr.HTML("<h2>📄 Source Citations</h2><p style='color:#94a3b8;'>Every answer is backed by exact document, page, and section</p>")
            with gr.Column(elem_classes=["glow-card"]):
                gr.HTML("<h2>🧠 Context Aware</h2><p style='color:#94a3b8;'>Remembers your conversation for natural follow-up questions</p>")
                
        gr.HTML("<div style='height: 40px;' id='features'></div>")
        gr.HTML("<h2 style='text-align:center;'>How It Works</h2>")
        with gr.Row():
            gr.HTML("<div style='text-align:center; padding:20px;'><h3 style='color:#6366f1;'>Step 1: Upload Documents</h3><p style='color:#94a3b8;'>Index your internal PDFs</p></div>")
            gr.HTML("<div style='text-align:center; padding:20px;'><h3 style='color:#6366f1;'>Step 2: Ask Anything</h3><p style='color:#94a3b8;'>Natural language questions</p></div>")
            gr.HTML("<div style='text-align:center; padding:20px;'><h3 style='color:#6366f1;'>Step 3: Get Answers</h3><p style='color:#94a3b8;'>Accurate answers with citations</p></div>")
            
        gr.HTML("<div style='background: var(--bg-card); padding: 20px; text-align: center; border-radius: 8px; margin: 40px 0;'><h3 style='margin:0; color:#a5b4fc;'>6 Documents Indexed | 20+ Test Cases | 90%+ Accuracy</h3></div>")
        gr.HTML("<p style='text-align:center; color:#64748b; font-size: 14px;'>Meridian © 2026 | Built for AnthraSync Technologies Pvt. Ltd.</p>")

    # === LOGIN PAGE ===
    with gr.Column(visible=False) as login_col:
        with gr.Column(elem_classes=["auth-card"]):
            gr.HTML("<h2 style='text-align:center; color:white; margin-bottom: 24px;'>Login to Meridian</h2>")
            login_err = gr.HTML("", elem_classes=["error-text"])
            user_in = gr.Textbox(label="Username", placeholder="Enter your username", elem_classes=["pill-input"])
            pwd_in = gr.Textbox(label="Password", type="password", placeholder="Enter your password", elem_classes=["pill-input"])
            login_btn = gr.Button("Sign In", elem_classes=["primary-btn"])
            gr.HTML("<p style='text-align:center; color:#94a3b8; font-size:12px; margin-top:16px;'>Demo credentials: admin / meridian123</p>")
            back_btn = gr.Button("← Back to Home")

    # === MAIN APP ===
    with gr.Column(visible=False) as app_col:
        with gr.Row(elem_classes=["meridian-header"]):
            with gr.Column(scale=4):
                gr.HTML(f"<div class='meridian-title-container'>{compass_svg}<h1 class='meridian-title'>Meridian</h1></div>")
            with gr.Column(scale=1, min_width=250):
                with gr.Row():
                    user_badge = gr.HTML("", elem_classes=["user-badge-container"])
                    logout_btn = gr.Button("Logout", elem_classes=["outline-red-btn"], size="sm")

        with gr.Row():
            with gr.Column(scale=1, min_width=280, elem_classes=["brand-sidebar"]):
                with gr.Tabs():
                    with gr.TabItem("📁 Documents"):
                        gr.Markdown("Click **Index Documents** below to scan `data/documents/`.")
                        doc_list = gr.HTML(value="<p style='color: #94A3B8; font-size: 13px;'>Loading documents...</p>")
                        ingest_btn = gr.Button("⚡ Index Documents", elem_classes=["primary-btn"])
                    
                    with gr.TabItem("💬 History"):
                        new_chat_btn = gr.Button("New Chat +", elem_classes=["primary-btn"])
                        gr.HTML("<hr style='border:0; border-top:1px solid #2a2a3e; margin: 12px 0;'/>")
                        
                        @gr.render(inputs=[username_state, session_id_state])
                        def render_history(uname, current_sid):
                            if not uname: return
                            sessions = ch.load_user_history(uname).get("sessions", [])
                            if not sessions:
                                gr.HTML("<p style='color:#94a3b8; font-size:13px; font-style:italic;'>No past chats.</p>")
                                return
                            
                            for s in sessions:
                                sid = s["session_id"]
                                msgs = s.get("messages", [])
                                title = "New Chat"
                                if msgs:
                                    first_user = next((m for m in msgs if m["role"]=="user"), None)
                                    if first_user:
                                        title = first_user["content"][:30] + "..." if len(first_user["content"])>30 else first_user["content"]
                                
                                label = f"{title} ({len(msgs)} msgs)\\n{s['started_at'][:10]}"
                                with gr.Row():
                                    active_cls = "session-active" if sid == current_sid else ""
                                    btn = gr.Button(label, elem_classes=["session-item", active_cls], scale=4)
                                    del_btn = gr.Button("🗑️", scale=1)
                                    
                                    btn.click(fn=load_session, inputs=[gr.State(uname), gr.State(sid)], outputs=[session_id_state, chatbot, read_only_state])
                                    def del_s(u, sess_id):
                                        ch.delete_session(u, sess_id)
                                        return sess_id
                                    del_btn.click(fn=del_s, inputs=[gr.State(uname), gr.State(sid)], outputs=[session_id_state])

            with gr.Column(scale=3):
                readonly_banner = gr.HTML("")
                chatbot = gr.Chatbot(label="Meridian Chat Console", height=550, render_markdown=True, avatar_images=(None, avatar_path))
                with gr.Row():
                    txt_input = gr.Textbox(show_label=False, placeholder="Ask a question...", scale=4, container=False, elem_classes=["pill-input"])
                    submit_btn = gr.Button("Send ➔", elem_classes=["primary-btn"], scale=1)

    # State toggles
    get_started_btn.click(lambda: (gr.update(visible=False), gr.update(visible=True)), outputs=[landing_col, login_col])
    back_btn.click(lambda: (gr.update(visible=True), gr.update(visible=False), ""), outputs=[landing_col, login_col, login_err])
    
    login_btn.click(
        fn=handle_login,
        inputs=[user_in, pwd_in],
        outputs=[login_col, app_col, user_badge, login_err, pwd_in, username_state, session_id_state, read_only_state, chatbot]
    )
    
    logout_btn.click(
        fn=handle_logout,
        outputs=[landing_col, login_col, app_col, user_in, pwd_in, username_state, session_id_state, chatbot]
    )
    
    def update_banner(is_ro):
        if is_ro: return "<div style='background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.3); color:#F59E0B; padding:8px 16px; border-radius:8px; margin-bottom:16px;'>⚠️ You are viewing a past session. Start a New Chat to ask questions.</div>"
        return ""
        
    read_only_state.change(fn=update_banner, inputs=[read_only_state], outputs=[readonly_banner])
    
    new_chat_btn.click(fn=start_new_session, inputs=[username_state], outputs=[session_id_state, chatbot, read_only_state])
    
    ingest_btn.click(fn=trigger_ingest, outputs=[doc_list])
    
    submit_btn.click(fn=handle_message, inputs=[txt_input, chatbot, username_state, session_id_state, read_only_state], outputs=[txt_input, chatbot])
    txt_input.submit(fn=handle_message, inputs=[txt_input, chatbot, username_state, session_id_state, read_only_state], outputs=[txt_input, chatbot])

    demo.load(fn=get_documents_html, outputs=[doc_list])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
