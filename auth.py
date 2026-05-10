import secrets
import string
import hashlib
import datetime
import firebase_client as db
import os
from dotenv import load_dotenv

load_dotenv()

LOCAL_ACCOUNTS = set()
# Default pepper for OOTB functionality
PEPPER = os.getenv("AUTH_PEPPER", "anonq-secure-v1-7f82b9c3")


def generate_account_number():
    parts = [''.join(secrets.choice(string.digits) for _ in range(4)) for _ in range(4)]
    return '-'.join(parts)


def hash_account(account_number: str) -> str:
    # Adding a pepper makes it harder to use pre-computed rainbow tables
    # for the 16-digit number space.
    raw = f"{account_number.strip()}{PEPPER}"
    return hashlib.sha256(raw.encode()).hexdigest()


def create_account() -> str:
    number = generate_account_number()
    hashed = hash_account(number)
    LOCAL_ACCOUNTS.add(hashed)
    try:
        db.set_document("accounts", hashed, {
            "created_at": datetime.datetime.now(tz=datetime.timezone.utc),
        })
    except Exception:
        pass
    return number


def login(account_number: str) -> str | None:
    hashed = hash_account(account_number)
    if hashed in LOCAL_ACCOUNTS:
        return hashed
    try:
        doc = db.get_document("accounts", hashed)
        if doc is not None:
            return hashed
    except Exception:
        pass
    return None


def is_admin(account_hash: str) -> bool:
    if not account_hash:
        return False
    try:
        # Check admins collection for the account hash
        doc = db.get_document("admins", account_hash)
        return doc is not None
    except Exception:
        return False
