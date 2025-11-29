from keep_alive import keep_alive 
import discord
from discord.ext import commands
import os

# ======================================================
# PHẦN 1: CẤU HÌNH VÀ CODE BOT DISCORD
# ======================================================

# BẮT BUỘC: Thay thế bằng ID Discord của bạn (Admin)
ID_ADMIN = 1065648216911122506


# Hàm đọc danh sách từ cấm từ file tucam.txt
def load_tu_cam(filename="tucam.txt"):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        print(
            f"Lỗi: Không tìm thấy file {filename}. Bot sẽ không kiểm tra từ cấm."
        )
        return []


TU_CAM = load_tu_cam()

# Thiết lập Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print('----------------------------------')
    print(f'🤖 Bot đã đăng nhập với tên: {bot.user}')
    print(f'🛡️ Admin ID được cấu hình: {ID_ADMIN}')
    print(f'🚫 Số lượng từ cấm đã tải: {len(TU_CAM)}')
    print('----------------------------------')


@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! Độ trễ: {round(bot.latency * 1000)}ms')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # --- CHỨC NĂNG 1: KIỂM TRA TỪ CẤM ---
    noi_dung_lower = message.content.lower()
    vi_pham_tu_cam = False

    for tu in TU_CAM:
        if tu in noi_dung_lower:
            vi_pham_tu_cam = True
            break

    if vi_pham_tu_cam:
        await message.channel.send(
            f"{message.author.mention}, bạn không được phép nhắn từ cấm!")
        try:
            admin_user = await bot.fetch_user(ID_ADMIN)
            await admin_user.send(
                f"⚠️ **Cảnh báo từ cấm**: Thành viên **{message.author}** đã nhắn từ cấm tại kênh {message.channel.mention}.\nNội dung: `{message.content}`"
            )
        except Exception as e:
            print(f"Lỗi khi gửi DM cho Admin: {e}")

    # --- CHỨC NĂNG 2: CHẶN TAG @EVERYONE ---
    if message.mention_everyone and message.author.id != ID_ADMIN:
        try:
            await message.delete()
            await message.channel.send(
                f"🚫 {message.author.mention}, bạn không có quyền tag @everyone/@here!"
            )
        except discord.Forbidden:
            await message.channel.send(
                f"🚫 {message.author.mention}, bạn không được tag everyone! (Bot thiếu quyền xóa)"
            )

        try:
            admin_user = await bot.fetch_user(ID_ADMIN)
            await admin_user.send(
                f"🛑 **Cảnh báo Tag Everyone**: Thành viên **{message.author}** đã cố tag everyone tại kênh {message.channel.mention}."
            )
        except Exception as e:
            print(f"Lỗi khi gửi DM cho Admin: {e}")

    await bot.process_commands(message)


# ======================================================
# PHẦN 2: KHỞI ĐỘNG CHƯƠNG TRÌNH
# ======================================================

# 1. Kích hoạt chức năng Keep Alive (Chạy Web Server trong luồng phụ)
import time 

# 1. Kích hoạt Web Server
keep_alive()

# 2. Chạy Bot Discord với cơ chế tự hồi sinh
if __name__ == "__main__":
    TOKEN = os.environ.get('DISCORD_TOKEN')

    if not TOKEN:
        print("❌ LỖI: Bạn chưa thêm DISCORD_TOKEN vào Secrets!")
    else:
        # Vòng lặp vô tận: Nếu bot tắt, nó sẽ tự bật lại
        while True:
            try:
                bot.run(TOKEN)
            except Exception as e:
                print(f"\n⚠️ Bot bị ngắt kết nối: {e}")
                print("🔄 Đang khởi động lại sau 10 giây...")
                time.sleep(10)
