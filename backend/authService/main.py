from fastapi import FastAPI
from pydantic import BaseModel
 
from tokenStore import verify_token
from jwtIssuer import issue_jwt
 
app = FastAPI(title="RootDuck Auth Service")
 
 
class VerifyTokenRequest(BaseModel):
  
    token: str
 
 
class VerifyTokenResponse(BaseModel):
    jwt: str
 
 
@app.get("/health")
def health():
    return {"status": "ok"}
 
 
@app.post("/verify-token", response_model=VerifyTokenResponse)
def verify_token_endpoint(request: VerifyTokenRequest):
   
    if not verify_token(request.token):
      
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid token")
 
    token = issue_jwt()
    return VerifyTokenResponse(jwt=token)