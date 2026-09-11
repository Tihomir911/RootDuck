
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from authMiddleware import require_valid_jwt

router = APIRouter()

# Адрес authService внутри docker-компоуз сети. Docker Compose поднимает
# для каждого сервиса DNS-имя, равное имени сервиса в docker-compose.yml —
# поэтому "http://auth-service:8000" резолвится в правильный контейнер
# без хардкода IP-адресов.
AUTH_SERVICE_URL = "http://auth-service:8000"


class ExchangeTokenRequest(BaseModel):
    token: str  # сырой токен от rootduck-agent sysconnect


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