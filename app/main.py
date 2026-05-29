from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.router import router
from app.tools.mock_db import init_db

app = FastAPI(
    title="Casa Alo's Bistro — AI Assistant",
    description="RAG-powered chatbot for Casa Alo's Bistro, Fredericksburg VA",
    version="1.0.0",
)

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

# Serve the frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
