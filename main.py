from keep_alive import keep_alive
import discord
from discord.ext import commands
import os
import asyncio
import time
import datetime # Cần cho chức năng Timeout (Mute)

# ======================================================
# PHẦN 1: TẢI CẤU HÌNH VÀ DỮ LIỆU
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
        print(f"⚠️ Lỗi: Không tìm thấy file {filename}. Không ai được miễn trừ.")
        return []

TU_CAM = load_tu_cam()
ALLOWED_USER_IDS = load_allowed_users()

# Thiết lập Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)
# --- THÊM CÂY LỆNH SLASH COMMANDS ---

# ======================================================
# PHẦN 2: SỰ KIỆN BOT VÀ CHỨC NĂNG KIỂM DUYỆT
# ======================================================

@bot.event
async def on_ready():
    # --- THIẾT LẬP TRẠNG THÁI "ĐANG XEM" ---
    activity = discord.Activity(
        name="Dev Quang Hiếu Đẹp Zai", 
        type=discord.ActivityType.playing # Thay Watching bằng Streaming, Playing, Listening tùy ý
    )
    await bot.change_presence(activity=activity)
    
    # --- ĐỒNG BỘ LỆNH VÀ IN LOG (Giữ nguyên) ---
    await bot.tree.sync() 
    print('----------------------------------')
    print(f'🤖 Bot đã đăng nhập: {bot.user}')
    print(f'🛡️ Admin ID: {ID_ADMIN}')
    print(f'🚫 Số lượng từ cấm: {len(TU_CAM)}')
    print(f'✅ Whitelist: {len(ALLOWED_USER_IDS)}')
    print('----------------------------------')

# --- LỆNH SLASH COMMAND MỚI ---
@bot.tree.command(name="ping", description="Kiểm tra độ trễ (latency) của Bot.")
async def ping_slash(interaction: discord.Interaction):
    # Lệnh slash command dùng interaction.response.send_message
    await interaction.response.send_message(f'Độ trễ: {round(bot.latency * 1000)}ms', ephemeral=True)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # --- ĐỊNH NGHĨA NGOẠI LỆ ---
    is_exempt = (message.author.bot) or \
                (message.author.id == ID_ADMIN) or \
                (message.author.id in ALLOWED_USER_IDS)

    # --- KIỂM TRA TỪ CẤM ---
    if not is_exempt:
        noi_dung = message.content.lower()
        vi_pham = False
        
        for tu in TU_CAM:
            if tu in noi_dung:
                vi_pham = True
                break
        
        if vi_pham:
            try:
                await message.delete()
                duration = datetime.timedelta(minutes=5)
                await message.author.timeout(duration) 
                
                msg = await message.channel.send(
                    f"🚫 {message.author.mention}, bị cấm chat 5 phút vì vi phạm từ cấm!")
                
                await asyncio.sleep(5)
                await msg.delete()
                
                admin = await bot.fetch_user(ID_ADMIN)
                await admin.send(f"⚠️ ĐÃ MUTE 5P: {message.author} đã vi phạm.")
                
            except discord.errors.Forbidden:
                await message.channel.send(f"❌ Bot thiếu quyền MUTE {message.author.mention}!")
                
            except Exception as e:
                if isinstance(e, discord.errors.HTTPException) and e.status == 429:
                    print("⚠️ Bị Rate Limit. Đang nghỉ 3 giây...")
                    await asyncio.sleep(3)
                else:
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
# PHẦN 3: KHỞI ĐỘNG HỆ THỐNG (AUTO-RESTART)
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
                print(f"\n⚠️ Bot bị crash: {e}. Đang tự động khởi động lại sau 10 giây...")
                time.sleep(10)
