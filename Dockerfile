FROM python:3.10-slim

# ใส่ build-essential และ libsodium-dev เพื่อให้ติดตั้ง PyNaCl ได้ 100%
RUN apt-get update && \
    apt-get install -y ffmpeg git build-essential python3-dev libffi-dev libsodium-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bubble_bot.py"]
