import discord
from discord.ext import commands
import os
import time
import edge_tts
import asyncio
from flask import Flask
from threading import Thread

# ==========================================
# ส่วนตรวจสอบระบบ (System Check) - แบบละเอียด
# ==========================================
print("\n" + "="*30)
print("--- SYSTEM STARTUP: BUBBLE BOT ---")
current_token = os.getenv('TOKEN')

if current_token:
    print(f"✅ ตรวจพบ Token แล้ว!")
    print(f"ℹ️ ความยาว Token: {len(current_token)} ตัวอักษร")
    # เช็กว่ามีช่องว่างหัวท้ายไหม
    if current_token.strip() != current_token:
        print("⚠️ เตือน: มีช่องว่าง (Space) ติดมากับ Token! กำลังลบออกอัตโนมัติ...")
else:
    print("❌ ไม่พบ Token! (ตัวแปร TOKEN เป็น None)")
    print("   -> กรุณาไปที่ Environment ใน Render แล้วเช็กชื่อตัวแปรว่าเขียน 'TOKEN' ถูกไหม")

print("="*30 + "\n")
# ==========================================

# --- ส่วน Web Server (Keep Alive) ---
app = Flask('')
@app.route('/')
def main():
    return "Bubble Bot is alive!"

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
is_speaking = False
active_text_channel_id = None
VOICE = 'th-TH-PremwadeeNeural'

@bot.event
async def on_ready():
    print(f'✅ Bubble Bot ({bot.user}) ออนไลน์แล้ว!')
    print(f'ID: {bot.user.id}')
    print('------')

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

@bot.command()
async def join(ctx):
    global active_text_channel_id
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        active_text_channel_id = ctx.channel.id
        await ctx.send(f"⚡ Bubble Bot มาแล้ว! อ่านห้อง **{ctx.channel.name}** ครับ")
    else:
        await ctx.send("❌ เข้าห้องเสียงก่อนครับ")

@bot.command()
async def leave(ctx):
    global is_speaking, active_text_channel_id
    if ctx.voice_client:
        tts_queue.clear()
        is_speaking = False
        active_text_channel_id = None
        await ctx.voice_client.disconnect()
        await ctx.send("👋 บาย")

@bot.event
async def on_message(message):
    global is_speaking
    if message.author.bot: return
    await bot.process_commands(message)

    if message.guild.voice_client and not message.content.startswith('!'):
        if active_text_channel_id is None or message.channel.id != active_text_channel_id:
            return
        if not message.content.strip(): return

        tts_queue.append(message.content)
        if not is_speaking:
            await play_next(message)

# ==========================================
# ส่วนรันระบบแบบใหม่ (Crash Reporting)
# ==========================================
import sys

# 1. เริ่ม Web Server
print(">> Step 1: Starting Web Server...", file=sys.stderr)
keep_alive()

# 2. เตรียม Token
token = os.getenv('TOKEN')
if not token:
    print("CRITICAL ERROR: TOKEN NOT FOUND! (ไม่เจอ Token ใน Environment)", file=sys.stderr)
    sys.exit(1) # สั่งปิดโปรแกรมทันที

# 3. เริ่มรันบอท (พร้อมดักจับ Error)
print(f">> Step 2: Attempting to login with Token ending in ...{token[-5:]}", file=sys.stderr)
print(">> PLEASE WATCH LOGS NOW...", file=sys.stderr)

try:
    # ลบช่องว่างหัวท้ายกันเหนียว
    bot.run(token.strip()) 
except Exception as e:
    # ถ้าบรรทัดนี้ทำงาน แสดงว่าบอทตาย -> สั่งปริ้น Error ตัวแดงทันที
    print(f"\n\n!!! FATAL ERROR: บอทเริ่มทำงานไม่ได้ !!!\nสาเหตุ: {e}\n\n", file=sys.stderr)
    # สั่งฆ่า Web Server ให้ตายตามไปด้วย (Render จะได้รู้ว่าพัง)
    os._exit(1)
