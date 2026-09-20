
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from authMiddleware import require_valid_jwt

router = APIRouter()

AUTH_SERVICE_URL = "http://auth-service:8000"


class ExchangeTokenRequest(BaseModel):
    token: str


class ExchangeTokenResponse(BaseModel):
    jwt: str


@router.post("/auth/exchange", response_model=ExchangeTokenResponse)
async def exchange_token(request: ExchangeTokenRequest):

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/verify-token",
                json={"token": request.token},
                timeout=5.0,
            )
        except httpx.RequestError:

            raise HTTPException(status_code=503, detail="Auth service unavailable")

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Invalid token")

    return ExchangeTokenResponse(**response.json())


@router.get("/system/metrics", dependencies=[Depends(require_valid_jwt)])
async def get_system_metrics():
    
    return {"status": "not_implemented_yet"}