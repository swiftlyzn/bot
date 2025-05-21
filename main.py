import discord
import requests
import asyncio
import json
import os
import datetime
import aiohttp
import asyncio
TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
# Lưu trữ cấu hình kênh và role cho mỗi server
config_file = "config.json"

# Kiểm tra xem file có tồn tại và hợp lệ không
if not os.path.exists(config_file) or os.path.getsize(config_file) == 0:
    server_configs = {}
    # Tạo một file JSON trống hợp lệ
    with open(config_file, "w") as file:
        json.dump(server_configs, file)
else:
    try:
        with open(config_file, "r") as file:
            server_configs = json.load(file)
    except json.JSONDecodeError:
        print("⚠️ File config.json bị lỗi, tạo lại một file mới.")
        server_configs = {}
        # Nếu bị lỗi, tạo lại file hợp lệ
        with open(config_file, "w") as file:
            json.dump(server_configs, file)

class VersionBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.old_win = ""
        self.old_rbtng = ""

    async def setup_hook(self):
        self.bg_task = asyncio.create_task(self.check_versions())

    async def on_ready(self):
        print(f"🤖 Bot đã hoạt động: {self.user}")
        await self.change_presence(activity=discord.Game(name="TNG Exploit ❤️"))

    async def on_guild_join(self, guild):
        # Khi bot được thêm vào server, yêu cầu người dùng chọn kênh và role
        await self.send_setup_message(guild)

    async def send_setup_message(self, guild):
        channel = guild.text_channels[0]
        await channel.send("👋 Chào! Hãy trả lời tin nhắn này với nội dung !setup")

    async def on_message(self, message):
        if self.user.mention in message.content:
            await message.channel.send("👋 Chào! Hãy trả lời tin nhắn này với nội dung `!setup` để bắt đầu setup.")
            return
        if message.author == self.user:
            return
        if message.content.startswith("!setup"):
            # Người dùng nhập lệnh setup để cấu hình kênh và role
            guild = message.guild
            if guild.id not in server_configs:
                server_configs[guild.id] = {}

            # Yêu cầu người dùng chọn kênh từ danh sách kênh hiện có
            await message.channel.send("Hãy trả lời tin nhắn này và chọn một kênh để nhận thông báo (hãy chọn một trong các kênh sau):")
            channels = [channel.name for channel in guild.text_channels]
            for idx, channel_name in enumerate(channels, start=1):
                await message.channel.send(f"{idx}. {channel_name}")

            def check_channel(msg):
                return msg.author == message.author and msg.content.isdigit() and 1 <= int(msg.content) <= len(channels)

            # Lấy tin nhắn người dùng chọn kênh
            msg = await self.wait_for('message', check=check_channel)
            channel_index = int(msg.content) - 1
            channel = guild.text_channels[channel_index]
            server_configs[guild.id]['channel'] = channel.id
            await message.channel.send(f"Cấu hình thành công! Kênh thông báo: {channel.name}")

            # Yêu cầu người dùng chọn role từ danh sách role hiện có
            await message.channel.send("Hãy trả lời tin nhắn này và chọn một role để nhận thông báo (hãy chọn một trong các role sau):")
            roles = [role.name for role in guild.roles]
            for idx, role_name in enumerate(roles, start=1):
                await message.channel.send(f"{idx}. {role_name}")

            def check_role(msg):
                return msg.author == message.author and msg.content.isdigit() and 1 <= int(msg.content) <= len(roles)

            # Lấy tin nhắn người dùng chọn role
            role_msg = await self.wait_for('message', check=check_role)
            role_index = int(role_msg.content) - 1
            role = guild.roles[role_index]
            server_configs[guild.id]['role'] = role.id
            await message.channel.send(f"Cấu hình thành công! Role: {role.name}")

            # Lưu lại thông tin cấu hình
            with open(config_file, "w") as file:
                json.dump(server_configs, file)

    async def check_versions(self):
        await self.wait_until_ready()

        while not self.is_closed():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://weao.xyz/api/versions/current") as resp:
                        win_data = await resp.json()

                    win_version = win_data.get("Windows")
                    win_time = win_data.get("WindowsDate")

                    if win_version != self.old_win:
                        embed = discord.Embed(
                            title="🚨 **Roblox Update** 🚨",
                            description="Đây là thông tin mới nhất về các phiên bản roblox cập nhật.",
                            color=discord.Color.red()
                        )
                        embed.add_field(name="Roblox-Windows", value=f"```{win_version}```", inline=False)
                        embed.add_field(name="Thời gian cập nhật", value=f"```{win_time}```", inline=False)
                        embed.add_field(
                            name="Tải về phiên bản mới",
                            value=f"[Download](https://roblox.get-fusion.com/install?Version={win_version})",
                            inline=False
                        )
                        embed.add_field(name="📌 Lưu ý", value="Nên sử dụng Roblox TNG để có thể dùng TNG mà không lỗi Version.", inline=False)
                        embed.set_thumbnail(url="https://i.ibb.co/TBsdNsPp/Roblox-TNG.png")
                        vietnam_tz = datetime.timezone(datetime.timedelta(hours=7))
                        current_time = datetime.datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S")
                        embed.set_footer(text=f"Gửi lúc: {current_time}")

                        for guild_id, config in server_configs.items():
                            guild = self.get_guild(int(guild_id))  # Đảm bảo id là int
                            if guild:
                                channel = guild.get_channel(config['channel'])
                                role = discord.utils.get(guild.roles, id=config['role'])
                                if channel and role:
                                    await channel.send(content=f"<@&{role.id}>", embed=embed)

                        print(f"📤 {win_version}")
                        self.old_win = win_version
                    else:
                        print(f"✅ {self.old_win}.")
            except Exception as e:
                print(f"⚠️ Lỗi khi kiểm tra: {e}")

            await asyncio.sleep(180)
client = VersionBot()
client.run(TOKEN)