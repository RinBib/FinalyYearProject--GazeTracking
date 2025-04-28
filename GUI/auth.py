# auth.py
import os, json
from argon2 import PasswordHasher, exceptions

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
USERS_FILE  = os.path.join(BASE_DIR, 'users.json')
ph = PasswordHasher()

def _load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def _save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def register_user(email: str, password: str, name: str) -> bool:
    
    users = _load_users()
    if email in users:
        return False
    users[email] = {
        "password": ph.hash(password),  # Argon2 salts+hashes internally
        "name":     name
    }
    _save_users(users)
    return True

def verify_user(email: str, password: str) -> bool:
    
    users = _load_users()
    rec = users.get(email)
    if not rec:
        return False
    try:
        return ph.verify(rec["password"], password)
    except exceptions.VerifyMismatchError:
        return False

def get_user_name(email: str) -> str:
    
    
    
    users = _load_users()
    rec = users.get(email)
    return rec.get("name", "") if rec else ""
