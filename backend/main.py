from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv

# Load environment variables before importing routers
# (routers may read env vars at module level)
load_dotenv()

from app.routers import trades, positions, auth

app = FastAPI(title="V3Trading API", version="0.1.0")

# Add session middleware (required for OAuth)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key")
)

# Configure CORS origins from environment
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(trades.router)
app.include_router(positions.router)

@app.get("/")
async def root():
    return {"message": "V3Trading API", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}
