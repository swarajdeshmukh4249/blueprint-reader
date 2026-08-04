FROM python:3.11-slim

# Install tesseract and other system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ifcopenshell separately (not on standard PyPI)
RUN pip install --no-cache-dir ifcopenshell --extra-index-url https://blenderbim.org/dist/

COPY . .

CMD ["python3", "start_server.py"]
