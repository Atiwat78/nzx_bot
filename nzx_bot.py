import discord
from discord.ext import commands
import os
import time
import edge_tts 
import asyncio
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def main():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ตั้งค่า Permission
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents)

# ตัวแปรเก็บคิวข้อความ
tts_queue = [] 

# --- (สำคัญ) ตัวล็อคสถานะ กันบอททำงานซ้อนกัน ---
is_speaking = False 

# เลือกเสียง
VOICE = 'th-TH-PremwadeeNeural'

@bot.event
async def on_ready():
    print(f'✅ บอท {bot.user} ออนไลน์ (โหมดไหลลื่น ไม่ตัดบท)!')

# --- ฟังก์ชันเล่นเสียง ---
async def play_next(ctx):
    global is_speaking
    
    # 1. เช็คว่ามีคิวเหลือไหม
    if not tts_queue:
        is_speaking = False # ปลดล็อคเมื่อคิวหมด
        return

    # 2. ล็อคสถานะไว้ บอกว่า "ฉันทำงานอยู่นะ"
    is_speaking = True
    
    # 3. ดึงข้อความ
    text = tts_queue.pop(0)
    
    if not text.strip():
        await play_next(ctx)
        return

    try:
        # ตั้งชื่อไฟล์ไม่ให้ซ้ำ
        filename = f"voice_{int(time.time() * 1000)}.mp3"
        
        # โหลดเสียงจาก Edge-TTS
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(filename)

        vc = ctx.guild.voice_client
        if vc:
            source = discord.FFmpegPCMAudio(source=filename, executable='./ffmpeg.exe')
            
            # เล่นเสียง และเมื่อจบให้ไปเรียกฟังก์ชันลบไฟล์
            vc.play(source, after=lambda e: cleanup_and_next(ctx, filename))
        else:
            # ถ้าบอทไม่อยู่ในห้องแล้ว ให้เคลียร์สถานะ
            is_speaking = False
            
    except Exception as e:
        print(f"Error: {e}")
        # ถ้า Error ให้ข้ามไปตัวต่อไป อย่าหยุดทำงาน
        await play_next(ctx)

def cleanup_and_next(ctx, filename):
    # ฟังก์ชันนี้ทำงานหลังจากพูดจบ
    try:
        if os.path.exists(filename):
            os.remove(filename)
    except:
        pass
    
    # เรียก play_next ให้ทำงานต่อทันที (Loop)
    bot.loop.create_task(play_next(ctx))

# --- คำสั่ง ---

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"⚡ บอทมาแล้ว! (พิมพ์รัวได้เลย ไม่ตัดบท)")
    else:
        await ctx.send("❌ เข้าห้องเสียงก่อนครับ")

@bot.command()
async def leave(ctx):
    global is_speaking
    if ctx.voice_client:
        tts_queue.clear()
        is_speaking = False # รีเซ็ตสถานะ
        await ctx.voice_client.disconnect()
        await ctx.send("👋 บาย")

@bot.event
async def on_message(message):
    global is_speaking

    if message.author.bot:
        return

    await bot.process_commands(message)

    if message.guild.voice_client and not message.content.startswith('!'):
        if not message.content.strip():
            return

        # 1. เอาข้อความใส่คิวอย่างเดียว
        tts_queue.append(message.content)

        # 2. เช็คที่ตัวแปร is_speaking แทน (เสถียรกว่าการเช็ค vc.is_playing)
        # ถ้าบอท "ไม่ได้ทำงานอยู่" ให้เริ่มระบบ Loop ใหม่
        # แต่ถ้า "ทำงานอยู่แล้ว" (is_speaking = True) ก็ไม่ต้องทำอะไร เดี๋ยว Loop เก่ามันจะวนมาอ่านคิวเอง
        if not is_speaking:
            await play_next(message)
            
keep_alive()
# ใส่ Token

bot.run(os.getenv('TOKEN'))

