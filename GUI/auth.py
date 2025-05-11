import os
import json
import re
from argon2 import PasswordHasher, exceptions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'users.json')
ph = PasswordHasher()

# Validate the password against security requirements
def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character."
    return None

# Load users from the JSON file
def _load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

# Save users to the JSON file
def _save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# Register a new user
def register_user(email: str, password: str, name: str) -> bool:
    # Validate password
    validation_error = validate_password(password)
    if validation_error:
        return False, validation_error
    
    users = _load_users()
    if email in users:
        return False, "Email already registered."

    users[email] = {
        "password": ph.hash(password),  # Argon2 salts+hashes internally
        "name": name
    }
    _save_users(users)
    return True, "User registered successfully."

# Verify user credentials
def verify_user(email: str, password: str) -> bool:
    users = _load_users()
    rec = users.get(email)
    if not rec:
        return False
    try:
        return ph.verify(rec["password"], password)
    except exceptions.VerifyMismatchError:
        return False

# Get the user's name by email
def get_user_name(email: str) -> str:
    users = _load_users()
    rec = users.get(email)
    return rec.get("name", "") if rec else ""

