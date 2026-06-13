"""
BlueprintIQ Configuration
All named constants and environment variables
"""
import os
from typing import List

# ─── FILE VALIDATION CONSTANTS ───
MAX_FILE_SIZE_MB = 50
MIN_PIXEL_DISTANCE = 5  # for scale calibration
MIN_IMAGE_DIMENSION = 100  # minimum image dimensions in pixels (100x100)
CONFIDENCE_HIGH = 0.80
CONFIDENCE_MEDIUM = 0.55
CONFIDENCE_LOW = 0.0
ROOM_MATCH_THRESHOLD = 0.60  # for floor comparison
SUPPORTED_TYPES = [".pdf", ".png", ".jpg", ".jpeg", ".dxf", ".dwg"]
SUPPORTED_FILE_TYPES = SUPPORTED_TYPES  # alias for backward compatibility
SUPPORTED_UNITS = ["m", "ft", "mm", "cm"]
MAX_FLOORS = 20
MAX_ROOMS_PER_FLOOR = 100

# ─── AI CONFIGURATION ───
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_FAST = "gemini-1.5-flash"
GEMINI_MODEL_ACCURATE = "gemini-1.5-pro"
GEMINI_MAX_RETRIES = 2
GEMINI_TIMEOUT_SECONDS = 60

# Groq Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL_FAST = "llama-3.2-11b-vision-preview"
GROQ_MODEL_ACCURATE = "llama-3.2-90b-vision-preview"
GROQ_MAX_RETRIES = 2
GROQ_TIMEOUT_SECONDS = 60

# Provider priority (tried in order)
AI_PROVIDERS = ["groq", "gemini"]  # Try Groq first, then Gemini

# ─── ALLOWED ROOM TYPES ───
ALLOWED_ROOM_TYPES = [
    "bedroom", "bathroom", "kitchen", "living_room", "dining_room",
    "corridor", "balcony", "store", "utility", "parking", "lobby",
    "office", "staircase", "lift", "terrace", "unknown"
]

# ─── WALL TYPES ───
ALLOWED_WALL_TYPES = ["load_bearing", "partition", "external", "unknown"]

# ─── STANDARD SCALES ───
STANDARD_SCALES = [1/20, 1/25, 1/50, 1/100, 1/200, 1/500]

# ─── DATABASE CONFIGURATION ───
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blueprint_reader.db")

# ─── SUPABASE CONFIGURATION ───
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ─── STORAGE CONFIGURATION ───
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # "local" or "supabase"
LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", "./uploads")
MAX_UPLOAD_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ─── AUTHENTICATION ───
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY", "")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")

# ─── ENVIRONMENT ───
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

# ─── CORS CONFIGURATION ───
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    FRONTEND_ORIGIN
]

# ─── RATE LIMITING ───
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_PERIOD_SECONDS = 60

# ─── ERROR CONFIGURATION ───
ERROR_VERBOSITY = "verbose" if DEBUG else "minimal"
