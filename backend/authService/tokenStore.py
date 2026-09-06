import hashlib
import hmac
import os

TOKEN_HASH_PATH = os.enviton.get("TOKEN_HASH_PATH", "/etc/rootduck/token.hash")

def _hash_token(token:str) -> str:
    
    return hashlib.sha256(token.encode()).hexdigest()

def _load_stored_hash()-> str:
    
    try:
        with open(TOKEN_HASH_PATH, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""
    
def verify_token(candidate_token: str) -> bool:
    
    stored_hash = _load_stored_hash()
    if not stored_hash:
        return False  
 
    candidate_hash = _hash_token(candidate_token)
    return hmac.compare_digest(candidate_hash, stored_hash)