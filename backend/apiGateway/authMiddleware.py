from fastapi import Header, HTTPException
 
from jwtVerifier import verify_jwt
 
 
def require_valid_jwt(authorization: str = Header(...)) -> None:
    
    scheme, _, token = authorization.partition(" ")
    
    if scheme != "Bearer" or not token:
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
 
    if not verify_jwt(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")