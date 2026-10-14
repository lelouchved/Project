import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from contextlib import asynccontextmanager

from backend.database import engine, Base
from backend.routers import (
    auth_routes, club_routes, budget_routes, event_routes,
    attendance_routes, assignment_routes, certificate_routes, report_routes
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="MSOT Club Activities & Governance Tracker",
    description="Live platform for multi-campus club lifecycle, rotating QR check-in, rubric evaluation, budget approvals and verifiable certificates.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file directories
os.makedirs("./uploads/logos", exist_ok=True)
os.makedirs("./uploads/deliverables", exist_ok=True)
os.makedirs("./uploads/receipts", exist_ok=True)
os.makedirs("./uploads/certificates", exist_ok=True)
os.makedirs("./frontend", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="./uploads"), name="uploads")
app.mount("/frontend", StaticFiles(directory="./frontend"), name="frontend")

# Include Routers
app.include_router(auth_routes.router)
app.include_router(club_routes.router)
app.include_router(budget_routes.router)
app.include_router(event_routes.router)
app.include_router(attendance_routes.router)
app.include_router(assignment_routes.router)
app.include_router(certificate_routes.router)
app.include_router(report_routes.router)

@app.get("/")
def serve_index():
    return FileResponse("./frontend/index.html")

@app.get("/verify/{cert_id}")
def serve_verification_page(cert_id: str):
    # Returns the standalone public verification web interface
    if os.path.exists("./frontend/verify.html"):
        return FileResponse("./frontend/verify.html")
    return FileResponse("./frontend/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
