from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.version import APP_VERSION


app = FastAPI(
    title=settings.app_name,
    description="Backend service for Novel2Script AI.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env, "version": APP_VERSION}


app.include_router(router, prefix=settings.api_prefix)
