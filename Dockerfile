FROM python:3.10-slim

# 1. ลงโปรแกรมเสียง (FFmpeg) และ Git
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# 2. ตั้งค่าโฟลเดอร์ทำงาน
WORKDIR /app

# 3. ก๊อปปี้ไฟล์ทั้งหมดเข้าเซิร์ฟเวอร์
COPY . .

# 4. ลง Library จาก requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5. สั่งรันบอท
CMD ["python", "bubble_bot.py"]
