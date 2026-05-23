import os

# Manual .env loading to avoid crash in certain Python environments
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ[k] = v

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from blueprint_logic import analyze_blueprint

app = FastAPI(title="AI Blueprint Reader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "AI Blueprint Reader API is running"}

@app.post("/analyze-blueprint")
async def analyze_blueprint_api(file: UploadFile = File(...)):
    file_bytes = await file.read()
    result = analyze_blueprint(file_bytes, file.filename or "")
    return result