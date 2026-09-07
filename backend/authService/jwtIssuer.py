import os
import time
from pathlib import Path
 
import jwt 

JWT_SECRET_PATH = os.environ.get("JWT_SECRET_PATH", "/data/jwt_secret.key")

JWT_TTL_SECONDS = 3600
 
ALGORITHM = "HS256"

def _load_or_create_secret() -> str:
    
    path = Path(JWT_SECRET_PATH)
    if path.exists():
        return path.read_text().strip()
    
    secret = os.urandom(32).hex()
 
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(secret)
    return secret


_SECRET = _load_or_create_secret()
 
 
def issue_jwt() -> str:
    
    now = int(time.time())
    payload = {
        "iat": now,
        "exp": now + JWT_TTL_SECONDS,
    }
    return jwt.encode(payload, _SECRET, algorithm=ALGORITHM)

def verify_jwt(token: str) -> bool:
    
    try:
        jwt.decode(token, _SECRET, algorithms=[ALGORITHM])
        return True
    except jwt.PyJWTError:
        return False