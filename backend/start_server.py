#!/usr/bin/env python3
import os
import sys

# Get PORT from environment, default to 8000 if not set
port = int(os.environ.get("PORT", "8000"))

# Start uvicorn with the correct port
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port)
