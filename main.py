from keep_alive import keep_alive
import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
import time
import datetime
import json

# ======================================================
# PHẦN 1: CẤU HÌNH VÀ DỮ LIỆU
# ======================================================

# --- BẠN CẦN ĐIỀN THÔNG TIN VÀO ĐÂY ---
ID_ADMIN = 1065648216911122506              # ID của bạn (Admin tối cao)
MUTE_LOG_CHANNEL_ID = 1444909829469634590   # ID kênh thông báo phạt Mute
WELCOME_CHANNEL_ID = 123456789012345678     # <--- THAY ID KÊNH CHÀO MỪNG
AUTO_ROLE_ID = 123456789012345678           # <--- THAY ID ROLE "THÀNH VIÊN"

# Tên các file dữ liệu
WARNING_FILE = "warnings.json"
TU_CAM_FILE = "tucam.txt"
WHITELIST_FILE = "id-user.txt"

# --- HÀM HỖ TRỢ ĐỌC/GHI FILE ---

def load_tu_cam(filename=TU_CAM_FILE):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"⚠️ Lỗi: Không tìm thấy file {filename}.")
        return []

def load_allowed_users(filename=WHITELIST_FILE):
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

def load_warnings():
    try:
        with open(WARNING_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_warnings(data):
    with open(WARNING_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Tải dữ liệu ban đầu
TU_CAM = load_tu_cam()
ALLOWED_USER_IDS = load_allowed_users()

# Thiết lập Intents (QUAN TRỌNG)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True   # Cần để chào mừng và kick/ban
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ======================================================
# PHẦN 2: SỰ KIỆN BOT (EVENTS)
# ======================================================

@bot.event
async def on_ready():
    # Đồng bộ lệnh Slash
    try:
        synced = await bot.tree.sync()
        print(f"✅ Đã đồng bộ {len(synced)} lệnh Slash.")
    except Exception as e:
        print(f"❌ Lỗi đồng bộ lệnh: {e}")
    
    activity = discord.Activity(
        name="Dev Quang Hiếu Đẹp Zai", 
        type=discord.ActivityType.watching
    )
    await bot.change_presence(activity=activity)
    
    print('----------------------------------')
    print(f'🤖 Bot đã đăng nhập: {bot.user}')
    print(f'🛡️ Admin ID (Super User): {ID_ADMIN}')
    print(f'🚫 Số lượng từ cấm: {len(TU_CAM)}')
    print('----------------------------------')

# --- SỰ KIỆN: THÀNH VIÊN MỚI VÀO ---
@bot.event
async def on_member_join(member):
    # 1. Gửi lời chào
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🎉 Chào mừng thành viên mới!",
            description=f"Xin chào {member.mention} đã đến với máy chủ!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Bạn là thành viên thứ {len(member.guild.members)}")
        await channel.send(embed=embed)

    # 2. Tự động cấp Role
    role = member.guild.get_role(AUTO_ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except Exception as e:
            print(f"❌ Không thể cấp role: {e}")

# --- SỰ KIỆN: THÀNH VIÊN RỜI ĐI ---
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f"😢 **{member.display_name}** đã rời khỏi server.")

# ======================================================
# PHẦN 3: CÁC LỆNH QUẢN LÝ (SLASH COMMANDS)
# ======================================================

# --- LỆNH PING ---
@bot.tree.command(name="ping", description="Kiểm tra độ trễ (latency)")
async def ping_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f'Độ trễ: {round(bot.latency * 1000)}ms')

# --- LỆNH KICK (CHỈ ADMIN) ---
@bot.tree.command(name="kick", description="Đuổi thành viên (Chỉ Admin)")
@app_commands.describe(member="Thành viên cần kick", reason="Lý do")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Không có lý do"):
    # Check ID Admin
    if interaction.user.id != ID_ADMIN:
        await interaction.response.send_message("❌ Mày tuổi gì đòi kick người? Chỉ Admin mới được dùng!", ephemeral=True)
        return

    if member.id == interaction.user.id:
        await interaction.response.send_message("❌ Sao lại tự kick mình thế?", ephemeral=True)
        return
    
    try:
        await member.kick(reason=reason)
        await interaction.response.send_message(f"👞 Đã sút **{member.name}** ra chuồng gà. Lý do: {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Bot không kick được (Quyền hạn thấp hơn đối phương).", ephemeral=True)

# --- LỆNH BAN (CHỈ ADMIN) ---
@bot.tree.command(name="ban", description="Cấm thành viên vĩnh viễn (Chỉ Admin)")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Vi phạm nghiêm trọng"):
    # Check ID Admin
    if interaction.user.id != ID_ADMIN:
        await interaction.response.send_message("❌ Lệnh này cấm trẻ em và người lạ!", ephemeral=True)
        return

    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"🔨 Đã BAN vĩnh viễn **{member.name}**. Lý do: {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Không thể ban người này.", ephemeral=True)

# --- LỆNH CLEAR (CHỈ ADMIN) ---
@bot.tree.command(name="clear", description="Xóa tin nhắn (Chỉ Admin)")
@app_commands.describe(amount="Số lượng tin nhắn cần xóa")
async def clear(interaction: discord.Interaction, amount: int):
    # Check ID Admin
    if interaction.user.id != ID_ADMIN:
        await interaction.response.send_message("❌ Đừng có nghịch xóa tin nhắn lung tung!", ephemeral=True)
        return

    if amount > 100:
        await interaction.response.send_message("❌ Chỉ xóa tối đa 100 tin mỗi lần.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Đã dọn dẹp **{len(deleted)}** tin nhắn.", ephemeral=True)

# --- LỆNH WARN (CHO PHÉP MOD DÙNG) ---
@bot.tree.command(name="warn", description="Cảnh cáo thành viên")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    warnings = load_warnings()
    user_id = str(member.id)
    if user_id not in warnings: warnings[user_id] = []
    
    warnings[user_id].append({
        "reason": reason, 
        "moderator": interaction.user.name, 
        "time": str(datetime.datetime.now())
    })
    save_warnings(warnings)
    
    embed = discord.Embed(title="⚠️ THÔNG BÁO CẢNH CÁO", color=discord.Color.orange())
    embed.add_field(name="Thành viên", value=member.mention, inline=False)
    embed.add_field(name="Lý do", value=reason, inline=False)
    embed.add_field(name="Số lần vi phạm", value=f"{len(warnings[user_id])}/3", inline=True)
    await interaction.response.send_message(embed=embed)

    # Phạt Mute nếu đủ 3 gậy
    if len(warnings[user_id]) >= 3:
         duration = datetime.timedelta(hours=1)
         try:
            await member.timeout(duration)
            await interaction.channel.send(f"🚫 **{member.name}** đã bị cảnh cáo 3 lần và bị Mute 1 tiếng!")
         except: pass

# --- LỆNH CHECKWARN ---
@bot.tree.command(name="checkwarn", description="Xem lịch sử cảnh cáo")
async def checkwarn(interaction: discord.Interaction, member: discord.Member):
    warnings = load_warnings()
    user_id = str(member.id)
    if user_id not in warnings or not warnings[user_id]:
        await interaction.response.send_message(f"✅ **{member.name}** chưa có cảnh cáo nào.")
        return

    embed = discord.Embed(title=f"Lịch sử cảnh cáo: {member.name}", color=discord.Color.red())
    for i, warn in enumerate(warnings[user_id], 1):
        embed.add_field(name=f"Lần {i}", value=f"Lý do: {warn['reason']}\nBởi: {warn['moderator']}", inline=False)
    await interaction.response.send_message(embed=embed)

# --- LỆNH USERINFO ---
@bot.tree.command(name="userinfo", description="Xem thông tin chi tiết thành viên")
async def userinfo(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=f"Thông tin: {member.name}", color=member.color)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Ngày tạo acc", value=member.created_at.strftime("%d/%m/%Y"), inline=False)
    embed.add_field(name="Ngày vào Server", value=member.joined_at.strftime("%d/%m/%Y"), inline=False)
    await interaction.response.send_message(embed=embed)

# ======================================================
# PHẦN 4: XỬ LÝ TIN NHẮN (GIỮ NGUYÊN CODE GỐC CỦA BẠN)
# ======================================================

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
        tu_cam_bi_phat_hien = [] 
        
        for tu in TU_CAM:
            if tu in noi_dung:
                tu_cam_bi_phat_hien.append(tu) 
        
        if tu_cam_bi_phat_hien:
            try:
                # 1. Tự động xóa tin nhắn
                await message.delete()
                
                # 2. Áp dụng Timeout (Mute) 5 phút
                duration = datetime.timedelta(minutes=5)
                await message.author.timeout(duration) 
                
                # 3. Gửi LOG CÔNG KHAI
                log_channel = bot.get_channel(MUTE_LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(
                        f"Thằng **{message.author.display_name}** đã bị mute 5 phút."
                    )
                
                # 4. Gửi cảnh báo tạm thời
                msg = await message.channel.send(
                    f"🚫 {message.author.mention}, bị cấm chat 5 phút vì vi phạm từ cấm!")
                await asyncio.sleep(5)
                await msg.delete()
                
                # 5. Báo cáo chi tiết cho Admin (DM)
                detected_words_str = ", ".join(tu_cam_bi_phat_hien)
                admin = await bot.fetch_user(ID_ADMIN)
                await admin.send(
                    f"⚠️ **Vi phạm**: {message.author.display_name} nhắn: `{message.content}` "
                    f"(từ cấm: {detected_words_str}). Đã mute chó này 5 phút"
                )
                
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
# PHẦN 5: CHẠY BOT
# ======================================================

keep_alive()

if __name__ == "__main__":
    TOKEN = os.environ.get('DISCORD_TOKEN')

    if not TOKEN:
        print("❌ LỖI: Thiếu DISCORD_TOKEN trong Environment Variables.")
    else:
        while True:
            try:
                bot.run(TOKEN)
            except Exception as e:
                print(f"\n⚠️ Bot bị crash: {e}. Đang tự động khởi động lại sau 10 giây...")
                time.sleep(10)
