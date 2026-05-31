import os

# Manual .env loading to avoid crash in certain Python environments
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ[k] = v

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Any, Optional

from blueprint_logic import analyze_blueprint
from rates.dsr_registry import list_schedules
from export.boq_export import export_csv, export_xlsx, export_pdf

app = FastAPI(title="AI Blueprint Reader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o for o in [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            os.environ.get("FRONTEND_ORIGIN", ""),
        ] if o
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


@app.get("/rate-schedules")
def rate_schedules():
    return {"schedules": list_schedules()}


@app.post("/analyze-blueprint")
async def analyze_blueprint_api(file: UploadFile = File(...)):
    file_bytes = await file.read()
    max_mb = int(os.environ.get("MAX_UPLOAD_MB", "150"))
    if len(file_bytes) > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {max_mb} MB limit. Compress or split the drawing.",
        )
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
