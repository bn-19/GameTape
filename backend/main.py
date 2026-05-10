from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.search import router as search_router

app = FastAPI(title="NBA Highlight Mode", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(search_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
