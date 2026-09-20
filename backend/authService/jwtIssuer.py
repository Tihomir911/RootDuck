import os
from pathlib import Path
 
import jwt
 
JWT_SECRET_PATH = os.environ.get("JWT_SECRET_PATH", "/data/jwt_secret.key")
ALGORITHM = "HS256"
 
 
def _load_secret() -> str:

    path = Path(JWT_SECRET_PATH)
    if not path.exists():
        raise RuntimeError(
            f"JWT secret не найден по пути {JWT_SECRET_PATH} — "
            "убедись, что authService уже запускался и создал файл"
        )
    return path.read_text().strip()
 
 
def verify_jwt(token: str) -> bool:
    try:
        secret = _load_secret()
        jwt.decode(token, secret, algorithms=[ALGORITHM])
        return True
    except (jwt.PyJWTError, RuntimeError):
        return False