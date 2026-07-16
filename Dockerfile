FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=10000

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 1. Install all your normal requirements (except dlib/face_recognition)
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# 2. Install the pre-compiled dlib binary and required dependencies
RUN pip install dlib-bin face_recognition_models click pillow numpy

# 3. Install face_recognition, forcing it to skip the memory-crashing build step
RUN pip install --no-deps face_recognition

COPY . .

EXPOSE 10000

CMD ["gunicorn", "--timeout", "120", "app:app", "--bind", "0.0.0.0:10000"]