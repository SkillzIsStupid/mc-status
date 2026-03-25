import discord
from discord import app_commands
from mcstatus import JavaServer
import asyncio
import os

TOKEN = os.getenv("TOKEN")

SERVER = "score-complexity.gl.joinmc.link"
PORT = 25565

ALLOWED_ROLE = "Admin"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

status_message_id = None
status_channel_id = None
last_status = None


# 🔹 Embed builder
def build_embed(online, players=0, max_players=0, names=[]):
    if online:
        embed = discord.Embed(
            title="🟢 Server Online",
            description=f"Players: {players}/{max_players}",
            color=0x22c55e
        )
        if names:
            embed.add_field(name="Players", value="\n".join(names), inline=False)
    else:
        embed = discord.Embed(
            title="🔴 Server Offline",
            description="Server unreachable",
            color=0xef4444
        )
    return embed


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await tree.sync()
    client.loop.create_task(monitor())


# 🔹 Setup command
@tree.command(name="setup", description="Setup downdetector in this channel")
async def setup(interaction: discord.Interaction):
    global status_message_id, status_channel_id

    # ✅ respond immediately (fixes timeout)
    await interaction.response.defer(ephemeral=True)

    try:
        channel = interaction.channel

        msg = await channel.send("🔄 Initializing status...")

        status_message_id = msg.id
        status_channel_id = channel.id

        await interaction.followup.send("✅ Downdetector setup complete!", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)


# 🔹 Monitor loop
async def monitor():
    global status_message_id, status_channel_id, last_status

    await client.wait_until_ready()

    while True:
        if not status_channel_id:
            await asyncio.sleep(5)
            continue

        channel = client.get_channel(status_channel_id)
        if not channel:
            await asyncio.sleep(5)
            continue

        try:
            server = JavaServer.lookup(f"{SERVER}:{PORT}")
            status = server.status()

            current_status = True
            players = status.players.online
            max_players = status.players.max
            names = [p.name for p in status.players.sample] if status.players.sample else []

        except:
            current_status = False
            players = 0
            max_players = 0
            names = []

        embed = build_embed(current_status, players, max_players, names)

        try:
            msg = await channel.fetch_message(status_message_id)
            await msg.edit(embed=embed)

        except:
            msg = await channel.send(embed=embed)
            status_message_id = msg.id

        # 🔴 Alert only when going DOWN
        if last_status is True and current_status is False:
            await channel.send(
                "@everyone 🔴 SERVER DOWN!",
                allowed_mentions=discord.AllowedMentions(everyone=True)
            )

        last_status = current_status
        await asyncio.sleep(10)


# 🔹 /status command
@tree.command(name="status", description="Check server status")
async def status_cmd(interaction: discord.Interaction):
    try:
        server = JavaServer.lookup(f"{SERVER}:{PORT}")
        status = server.status()

        players = status.players.online
        max_players = status.players.max
        names = [p.name for p in status.players.sample] if status.players.sample else []

        embed = build_embed(True, players, max_players, names)
    except:
        embed = build_embed(False)

    await interaction.response.send_message(embed=embed)


# 🔹 /maintenance command
@tree.command(name="maintenance", description="Send maintenance announcement")
@app_commands.describe(message="Maintenance message")
async def maintenance(interaction: discord.Interaction, message: str):

    await interaction.response.defer(ephemeral=True)

    if not any(role.name == ALLOWED_ROLE for role in interaction.user.roles):
        await interaction.followup.send("❌ No permission", ephemeral=True)
        return

    embed = discord.Embed(
        title="🛠️ Maintenance",
        description=message,
        color=0xf59e0b
    )

    await interaction.followup.send("✅ Announcement sent", ephemeral=True)

    channel = interaction.channel

    await channel.send(
        "@everyone",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(everyone=True)
    )


client.run(TOKEN)
