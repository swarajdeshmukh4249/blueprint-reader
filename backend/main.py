import os


allow_origins=[
    "https://archvision.me",
    "https://www.archvision.me",
]
# Manual .env loading to avoid crash in certain Python environments
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ[k] = v

# Set GOOGLE_API_KEY from GEMINI_API_KEY if GOOGLE_API_KEY is not set
if not os.environ.get("GOOGLE_API_KEY") and os.environ.get("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Any, Optional

from blueprint_logic import analyze_blueprint
from rates.dsr_registry import list_schedules
from export.boq_export import export_csv, export_xlsx, export_pdf
from api import organizations_router, projects_router, files_router, analysis_router, diff_router, correction_router, calibration_router, audit_router, comments_router, cost_engine_router, rate_cards_router, approvals_router, analytics_router, blueprint_files_router, floor_comparison_router, public_shares_router, cost_benchmark_router, room_editor_router
from auth.clerk import get_current_user, verify_jwt
from utils.error_handler import setup_error_handlers

app = FastAPI(title="AI Blueprint Reader API")

# Setup error handlers for consistent error response shape
setup_error_handlers(app)

# Include new enterprise API routes
app.include_router(organizations_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(diff_router, prefix="/api/v1")
app.include_router(correction_router, prefix="/api/v1")
app.include_router(calibration_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(comments_router, prefix="/api/v1")
app.include_router(cost_engine_router, prefix="/api/v1")
app.include_router(rate_cards_router, prefix="/api/v1")
app.include_router(approvals_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(blueprint_files_router, prefix="/api/v1")
app.include_router(floor_comparison_router, prefix="/api/v1")
app.include_router(public_shares_router, prefix="/api/v1")
app.include_router(cost_benchmark_router, prefix="/api/v1")
app.include_router(room_editor_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://archvision.me",
        "https://www.archvision.me",
        "http://localhost:3000",       # keep for local dev
        "http://localhost:5173",       # keep for local dev
        "http://localhost:5174",       # additional local dev port
        "http://localhost:5175",       # additional local dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExportRequest(BaseModel):
    items: list[dict[str, Any]]
    summary: Optional[dict[str, Any]] = None
    gst_breakdown: Optional[dict[str, Any]] = None
    company_name: str = "Blueprint Reader BOQ"
    letterhead_line: str = ""
    format: str = "csv"


@app.get("/")
def home():
    return {"message": "AI Blueprint Reader API is running"}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ArchVision API"}


@app.get("/rate-schedules")
def rate_schedules():
    return {"schedules": list_schedules()}


@app.post("/analyze-blueprint")
async def analyze_blueprint_api(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    # Optional authentication - if token provided, verify it
    if authorization:
        try:
            token = authorization.replace("Bearer ", "")
            await verify_jwt(token)
        except Exception:
            # If token verification fails, still allow the request for now
            pass

    file_bytes = await file.read()
    max_mb = int(os.environ.get("MAX_UPLOAD_MB", "150"))
    if len(file_bytes) > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {max_mb} MB limit. Compress or split the drawing.",
        )

    # Use the traditional blueprint_logic analyzer which returns room_data with proper structure
    result = analyze_blueprint(file_bytes, file.filename or "")
    return result


@app.post("/export/boq")
def export_boq_api(body: ExportRequest):
    summary = body.summary or body.gst_breakdown
    fmt = (body.format or "csv").lower()
    try:
        if fmt == "csv":
            data = export_csv(body.items, summary)
            return Response(
                content=data,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=boq.csv"},
            )
        if fmt in ("xlsx", "excel"):
            data = export_xlsx(body.items, summary, body.company_name)
            return Response(
                content=data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=boq.xlsx"},
            )
        if fmt == "pdf":
            data = export_pdf(
                body.items,
                summary,
                body.company_name,
                body.letterhead_line,
            )
            return Response(
                content=data,
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=boq.pdf"},
            )
        raise HTTPException(status_code=400, detail="format must be csv, xlsx, or pdf")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
