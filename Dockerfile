FROM python:3.10-slim

# 1. ลงเครื่องมือเสียงแบบจัดเต็ม (ผมเพิ่ม libopus0 สำหรับถอดรหัสเสียง Discord เข้าไปด้วย)
RUN apt-get update && \
    apt-get install -y ffmpeg git build-essential python3-dev libffi-dev libsodium-dev libopus0 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

# 2. บังคับติดตั้งระบบเสียงของ Discord และ PyNaCl ตรงๆ ไปเลย (กัน Render โหลดพลาด)
RUN pip install --no-cache-dir "discord.py[voice]" PyNaCl edge-tts flask

# 3. เผื่อไฟล์ requirements.txt ไว้
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bubble_bot.py"]
