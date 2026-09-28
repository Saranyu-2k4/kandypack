import re
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from psycopg.errors import UniqueViolation
from db import execute_query, fetch_one, safe_fetch_one

ph = PasswordHasher()
EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

def is_valid_email(email: str) -> bool:
    return bool(re.match(EMAIL_REGEX, email))

def register_user(name: str, email: str, password: str, confirm_password: str):
    clean_email = email.strip().lower()

    if not clean_email or not password or not confirm_password:
        return None, "All fields are required."
    if not is_valid_email(clean_email):
        return None, "Please enter a valid email address."
    if len(password) < 8:
        return None, "Password must be at least 8 characters long."
    if password != confirm_password:
        return None, "Passwords do not match."

    password_hash = ph.hash(password)
    try:
        user = fetch_one(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING *;",
            (name, email, password_hash)
        )
    except UniqueViolation:
        return None, "An account with this email already exists."
    except:
        return None, "An error occurred while creating the account. Please try again."
    return user, "Account created successfully! Please sign in."

def login_user(email: str, password: str):
    clean_email = email.strip().lower()

    if not clean_email or not password:
        return None, "Please provide both email and password."
    if not is_valid_email(clean_email):
        return None, "Please enter a valid email address."

    try:
        user = fetch_one("SELECT id, email, password_hash FROM users WHERE email = %s;", (email,))
        if not user:
            return None, "Invalid email or password."
    except Exception as e:
        print(f"DB Error: {e}")
        return None, "An error occurred while signing in. Please try again."

    try:
        ph.verify(user.password_hash, password)
        if ph.check_needs_rehash(user.password_hash):
            new_hash = ph.hash(password)
            execute_query("UPDATE users SET password_hash = %s WHERE id = %s;", (new_hash, user.id))
        return user, "Login successful!"
    except (VerifyMismatchError, InvalidHashError):
        return None, "Invalid email or password."
    except Exception as e:
        print(f"Pwd: {e}")
    return None, "An error occurred while signing in. Please try again."
