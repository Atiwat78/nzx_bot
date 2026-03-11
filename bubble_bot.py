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
    # ใช้ Port ตามที่ Render กำหนด หรือ 8080
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
# -----------------------------------

# --- ตั้งค่า Permission (เปิดรับทุกสิทธิ์เพื่อให้บอทเห็นทุกอย่าง) ---
intents = discord.Intents.all() 

bot = commands.Bot(command_prefix='!', intents=intents)

# ตัวแปรเก็บคิวข้อความ
tts_queue = [] 

# ตัวล็อคสถานะ กันบอททำงานซ้อนกัน
is_speaking = False 

# ตัวแปรจำห้องที่จะให้อ่าน
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
        # เช็คให้ชัวร์ว่าบอทยังเชื่อมต่อกับห้องเสียงอยู่
        if vc and vc.is_connected():
            source = discord.FFmpegPCMAudio(source=filename)
            vc.play(source, after=lambda e: cleanup_and_next(ctx, filename))
        else:
            is_speaking = False
            
    except Exception as e:
        print(f"Error ตอนเล่นเสียง: {e}")
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
    global active_text_channel_id 

    if ctx.author.voice:
        channel = ctx.author.voice.channel
        try:
            # สั่งให้เข้าห้องเสียง
            if ctx.voice_client is not None:
                await ctx.voice_client.move_to(channel)
            else:
                await channel.connect()
            
            # จำ ID ห้องแชทที่พิมพ์คำสั่ง
            active_text_channel_id = ctx.channel.id 
            
            await ctx.send(f"⚡ บอทมาแล้ว! จะอ่านข้อความจากห้อง **{ctx.channel.name}** เท่านั้นนะ")
        except Exception as e:
            # ถ้าเข้าไม่ได้ จะแจ้ง Error ในแชทเลย
            await ctx.send(f"❌ บอทเข้าห้องไม่ได้ครับ (Error: {e})")
            print(f"Join Error: {e}")
    else:
        await ctx.send("❌ คุณต้องเข้าไปอยู่ในห้องเสียงก่อนครับ")

@bot.command()
async def leave(ctx):
    global is_speaking, active_text_channel_id
    if ctx.voice_client:
        tts_queue.clear()
        is_speaking = False
        active_text_channel_id = None 
        
        await ctx.voice_client.disconnect()
        await ctx.send("👋 บาย")
    else:
        await ctx.send("❌ บอทยังไม่ได้อยู่ในห้องเสียงเลย")

@bot.event
async def on_message(message):
    global is_speaking

    if message.author.bot:
        return

    # คำสั่ง ! ต้องทำงานได้เสมอ
    await bot.process_commands(message)

    # กรองเฉพาะตอนบอทอยู่ในห้อง และไม่ใช่คำสั่ง
    if message.guild.voice_client and not message.content.startswith('!'):
        
        if active_text_channel_id is None or message.channel.id != active_text_channel_id:
            return 

        if not message.content.strip():
            return

        tts_queue.append(message.content)

        if not is_speaking:
            await play_next(message)

# รัน Web Server กันหลับ
keep_alive()

# --- ดึง Token มารัน ---
my_secret = os.getenv('TOKEN')

if my_secret is None:
    print("❌ Error: ไม่เจอ Token! (เช็กชื่อตัวแปรใน Render ด่วน)")
else:
    print(f"✅ เจอ Token แล้ว... (กำลังพยายาม Login)")
    try:
        bot.run(my_secret)
    except Exception as e:
        print(f"❌ Login พังเพราะ: {e}")
