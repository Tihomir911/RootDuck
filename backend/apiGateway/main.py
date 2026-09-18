from fastapi import FastAPI

from routes import router

app = FastAPI(title = "RootDock API Gateway")
app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}
