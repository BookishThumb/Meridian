USERS = {
    "admin": "meridian123",
    "demo": "demo123",
    "recruiter": "anthrasync2026"
}

def authenticate(username, password):
    if username in USERS and USERS[username] == password:
        return True
    return False
