FROM python:3.13-slim

WORKDIR /app

# Cài đặt dependencies hệ thống cần thiết cho psycopg2 và build tools
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    make \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code
COPY . .

# Chạy ứng dụng
CMD gunicorn app:app --bind 0.0.0.0:$PORT
