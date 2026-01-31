from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.models import Base
from app.database import engine
from app.routers import sessions, inventory, checkout, detect
from config import config

# Create tables
Base.metadata.create_all(bind=engine)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting VisionScan POS API...")
    yield
    # Shutdown
    print("Shutting down VisionScan POS API...")


# Initialize FastAPI app
app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Include routers
app.include_router(sessions.router)
app.include_router(inventory.router)
app.include_router(checkout.router)
app.include_router(detect.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG,
    )
