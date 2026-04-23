FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Tạo thư mục data và cấp quyền
RUN mkdir -p /app/data && chmod 777 /app/data

CMD gunicorn app:app --bind 0.0.0.0:$PORT
