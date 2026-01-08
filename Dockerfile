FROM python:3.10-slim

# ติดตั้ง FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# ตั้งค่าโฟลเดอร์ทำงาน
WORKDIR /app

# ก๊อปปี้ไฟล์ทั้งหมดเข้า Server
COPY . .

# ติดตั้งไลบรารี Python
RUN pip install --no-cache-dir -r requirements.txt

# สั่งรันบอท
CMD ["python", "nzx_bot.py"]