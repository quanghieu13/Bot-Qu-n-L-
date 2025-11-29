from keep_alive import keep_alive
import discord
from discord.ext import commands
import os
import asyncio
import time

# ======================================================
# PHẦN 1: CẤU HÌNH
# ======================================================

ID_ADMIN = 1065648216911122506

def load_tu_cam(filename="tucam.txt"):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"⚠️ Lỗi: Không tìm thấy file {filename}.")
        return []

def load_allowed_users(filename="id-user.txt"):
    allowed_ids = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.isdigit():
                    allowed_ids.append(int(line))
        return allowed_ids
    except FileNotFoundError:
        print(f"⚠️ Lỗi: Không tìm thấy file {filename}.")
        return []

TU_CAM = load_tu_cam()
ALLOWED_USER_IDS = load_allowed_users()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ======================================================
# PHẦN 2: SỰ KIỆN BOT
# ======================================================

@bot.event
async def on_ready():
    print('----------------------------------')
    print(f'🤖 Bot: {bot.user}')
    print(f'🛡️ Admin ID: {ID_ADMIN}')
    print(f'🚫 Từ cấm: {len(TU_CAM)}')
    print(f'✅ Whitelist: {len(ALLOWED_USER_IDS)}')
    print('----------------------------------')

@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Logic Whitelist
    is_allowed = (message.author.id == ID_ADMIN) or (message.author.id in ALLOWED_USER_IDS)

    # --- KIỂM TRA TỪ CẤM ---
    if not is_allowed:
        noi_dung = message.content.lower()
        vi_pham = False
        for tu in TU_CAM:
            if tu in noi_dung:
                vi_pham = True
                break
        
        if vi_pham:
            try:
                await message.delete()
                msg = await message.channel.send(f"🚫 {message.author.mention} nhắn từ cấm!")
                await asyncio.sleep(5)
                await msg.delete()
                
                admin = await bot.fetch_user(ID_ADMIN)
                await admin.send(f"⚠️ **Vi phạm**: {message.author} nhắn: `{message.content}`")
            except Exception as e:
                print(f"Lỗi xử lý từ cấm: {e}")
            return

    # --- CHẶN TAG EVERYONE ---
    if message.mention_everyone and message.author.id != ID_ADMIN:
        try:
            await message.delete()
            msg = await message.channel.send(f"🚫 {message.author.mention} không được tag all!")
            await asyncio.sleep(5)
            await msg.delete()
        except Exception:
            pass

    await bot.process_commands(message)

# ======================================================
# PHẦN 3: KHỞI ĐỘNG
# ======================================================

keep_alive()

if __name__ == "__main__":
    TOKEN = os.environ.get('DISCORD_TOKEN')
    if not TOKEN:
        print("❌ LỖI: Thiếu DISCORD_TOKEN.")
    else:
        while True:
            try:
                bot.run(TOKEN)
            except Exception as e:
                print(f"⚠️ Bot crash: {e}. Restarting in 10s...")
                time.sleep(10)
