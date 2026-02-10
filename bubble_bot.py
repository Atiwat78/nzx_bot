import discord
from discord.ext import commands
import os
import time
import edge_tts 
import asyncio
from flask import Flask
from threading import Thread

# --- ส่วน Web Server (Keep Alive) ---
app = Flask('')
@app.route('/')
def main():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# -----------------------------------

# ตั้งค่า Permission
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents)

# ตัวแปรเก็บคิวข้อความ
tts_queue = [] 

# ตัวล็อคสถานะ กันบอททำงานซ้อนกัน
is_speaking = False 

# --- (เพิ่มใหม่) ตัวแปรจำห้องที่จะให้อ่าน ---
active_text_channel_id = None

# เลือกเสียง
VOICE = 'th-TH-PremwadeeNeural'

@bot.event
async def on_ready():
    print(f'✅ บอท {bot.user} ออนไลน์ (โหมดอ่านเฉพาะห้องที่เรียก)!')

# --- ฟังก์ชันเล่นเสียง ---
async def play_next(ctx):
    global is_speaking
    
    if not tts_queue:
        is_speaking = False 
        return

    is_speaking = True
    text = tts_queue.pop(0)
    
    if not text.strip():
        await play_next(ctx)
        return

    try:
        filename = f"voice_{int(time.time() * 1000)}.mp3"
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(filename)

        vc = ctx.guild.voice_client
        if vc:
            # Render ใช้ Linux ไม่ต้องระบุ path ffmpeg.exe
            source = discord.FFmpegPCMAudio(source=filename)
            vc.play(source, after=lambda e: cleanup_and_next(ctx, filename))
        else:
            is_speaking = False
            
    except Exception as e:
        print(f"Error: {e}")
        await play_next(ctx)

def cleanup_and_next(ctx, filename):
    try:
        if os.path.exists(filename):
            os.remove(filename)
    except:
        pass
    bot.loop.create_task(play_next(ctx))

# --- คำสั่ง ---

@bot.command()
async def join(ctx):
    global active_text_channel_id # เรียกใช้ตัวแปรจำห้อง

    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        
        # (สำคัญ) จำ ID ของห้องที่พิมพ์คำสั่งนี้
        active_text_channel_id = ctx.channel.id 
        
        await ctx.send(f"⚡ บอทมาแล้ว! จะอ่านข้อความจากห้อง **{ctx.channel.name}** เท่านั้นนะ")
    else:
        await ctx.send("❌ เข้าห้องเสียงก่อนครับ")

@bot.command()
async def leave(ctx):
    global is_speaking, active_text_channel_id
    if ctx.voice_client:
        tts_queue.clear()
        is_speaking = False
        
        # (สำคัญ) ล้างค่าห้องเมื่อบอทออก
        active_text_channel_id = None 
        
        await ctx.voice_client.disconnect()
        await ctx.send("👋 บาย")

@bot.event
async def on_message(message):
    global is_speaking

    if message.author.bot:
        return

    # ให้คำสั่ง ! ทำงานได้เสมอ (แม้ผิดห้อง)
    await bot.process_commands(message)

    if message.guild.voice_client and not message.content.startswith('!'):
        
        # --- (จุดคัดกรอง) ---
        # ถ้ายังไม่มีใครเรียก (!join) หรือ ห้องที่พิมพ์มา ไม่ตรงกับห้องที่จำไว้
        if active_text_channel_id is None or message.channel.id != active_text_channel_id:
            return # จบการทำงาน ไม่ต้องอ่าน
        # ------------------

        if not message.content.strip():
            return

        tts_queue.append(message.content)

        if not is_speaking:
            await play_next(message)
            
# ... (โค้ดด้านบนเหมือนเดิม) ...

# รัน Web Server กันหลับ
keep_alive()

# --- ส่วนที่แก้เพิ่ม (Debug) ---
my_secret = os.getenv('TOKEN')

if my_secret is None:
    print("❌ Error: ไม่เจอ Token! (เช็กชื่อตัวแปรใน Render ด่วน)")
else:
    print(f"✅ เจอ Token แล้ว: {my_secret[:5]}... (กำลังพยายาม Login)")
    try:
        bot.run(my_secret)
    except Exception as e:
        print(f"❌ Login พังเพราะ: {e}")
