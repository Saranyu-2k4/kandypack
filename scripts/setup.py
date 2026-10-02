import secrets
import string
import os

def generate_secure_password(length=32):
    characters = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

DB_PASSWORD = generate_secure_password()
COOKIE_NAME = "auth_cookie"
COOKIE_KEY = generate_secure_password()
COOKIE_EXPIRY_DAYS = 30
DATABASE_URL = f"postgresql://postgres:{DB_PASSWORD}@db:5432/kandypack"

os.makedirs("secrets", exist_ok=True)
with open("secrets/db_password.txt", "w") as f:
    f.write(DB_PASSWORD)
os.makedirs(".streamlit", exist_ok=True)
with open(".streamlit/secrets.toml", "w") as f:
    f.write(f"""COOKIE_NAME = "{COOKIE_NAME}"
COOKIE_KEY = "{COOKIE_KEY}"
COOKIE_EXPIRY_DAYS = {COOKIE_EXPIRY_DAYS}
DATABASE_URL = "{DATABASE_URL}"
""")
with open(".env", "w") as f:
    f.write(f"""COOKIE_NAME="{COOKIE_NAME}"
COOKIE_KEY="{COOKIE_KEY}"
COOKIE_EXPIRY_DAYS={COOKIE_EXPIRY_DAYS}
DATABASE_URL="{DATABASE_URL}"
""")

os.system("docker compose down -v")
os.system("docker compose up -d")
