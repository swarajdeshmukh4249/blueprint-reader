FROM python:3.11-slim

# System deps + LibreDWG (dwg2dxf). Debian has no libredwg-tools package;
# build from the GNU release tarball so DWG conversion works on Railway.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    automake \
    autoconf \
    libtool \
    pkg-config \
    curl \
    ca-certificates \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && curl -fsSL https://ftp.gnu.org/gnu/libredwg/libredwg-0.13.3.tar.xz -o /tmp/libredwg.tar.xz \
    && tar -xJf /tmp/libredwg.tar.xz -C /tmp \
    && cd /tmp/libredwg-0.13.3 \
    && ./configure --disable-bindings --disable-python \
    && make -j"$(nproc)" \
    && make install \
    && ldconfig \
    && rm -rf /tmp/libredwg* \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "supabase_worker.py"]
