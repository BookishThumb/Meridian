import os
import json
import uuid
from datetime import datetime

HISTORY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "chat_history"))

def _get_file_path(username: str) -> str:
    return os.path.join(HISTORY_DIR, f"{username}.json")

def load_user_history(username: str) -> dict:
    path = _get_file_path(username)
    if not os.path.exists(path):
        return {"username": username, "sessions": []}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"username": username, "sessions": []}

def save_user_history(username: str, data: dict):
    os.makedirs(HISTORY_DIR, exist_ok=True)
    with open(_get_file_path(username), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def create_new_session(username: str) -> str:
    data = load_user_history(username)
    session_id = str(uuid.uuid4())
    new_session = {
        "session_id": session_id,
        "started_at": datetime.utcnow().isoformat(),
        "messages": []
    }
    # Insert at beginning so newest is first
    data["sessions"].insert(0, new_session)
    save_user_history(username, data)
    return session_id

def save_message(username: str, session_id: str, role: str, content: str, sources=None, confidence=None):
    data = load_user_history(username)
    for session in data["sessions"]:
        if session["session_id"] == session_id:
            msg = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }
            if sources is not None:
                msg["sources"] = sources
            if confidence is not None:
                msg["confidence"] = confidence
            session["messages"].append(msg)
            break
    save_user_history(username, data)

def delete_session(username: str, session_id: str):
    data = load_user_history(username)
    data["sessions"] = [s for s in data["sessions"] if s["session_id"] != session_id]
    save_user_history(username, data)
    
def get_session_messages(username: str, session_id: str) -> list:
    data = load_user_history(username)
    for session in data["sessions"]:
        if session["session_id"] == session_id:
            return session.get("messages", [])
    return []
