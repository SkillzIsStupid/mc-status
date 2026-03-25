import discord
from discord import app_commands
from mcstatus import JavaServer
import asyncio
import os

TOKEN = os.getenv("TOKEN")

SERVER = "score-complexity.gl.joinmc.link"
PORT = 25565

CHANNEL_NAME = "downdetector"
ALLOWED_ROLE = "Admin"  # change this

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

last_status = None
status_message = None


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
            description="Server is currently unreachable",
            color=0xef4444
        )
    return embed


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await tree.sync()
    client.loop.create_task(monitor())


async def monitor():
    global last_status, status_message

    await client.wait_until_ready()

    while True:
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

        for guild in client.guilds:
            for channel in guild.text_channels:
                if channel.name == CHANNEL_NAME:

                    embed = build_embed(current_status, players, max_players, names)

                    # 🔹 Create or update static message
                    if status_message is None:
                        status_message = await channel.send(embed=embed)
                    else:
                        try:
                            await status_message.edit(embed=embed)
                        except:
                            status_message = await channel.send(embed=embed)

                    # 🔴 Ping only when going DOWN
                    if last_status is True and current_status is False:
                        await channel.send("@everyone 🔴 SERVER DOWN!")

        last_status = current_status
        await asyncio.sleep(10)


# 🔹 Slash command: /status
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


# 🔹 Slash command: /maintenance (role restricted)
@tree.command(name="maintenance", description="Send maintenance announcement")
@app_commands.describe(message="Maintenance message")
async def maintenance(interaction: discord.Interaction, message: str):

    # 🔒 Role check
    roles = [role.name for role in interaction.user.roles]

    if ALLOWED_ROLE not in roles:
        await interaction.response.send_message("❌ You don't have permission.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🛠️ Maintenance",
        description=message,
        color=0xf59e0b
    )

    await interaction.response.send_message("✅ Announcement sent", ephemeral=True)

    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.name == CHANNEL_NAME:
                await channel.send("@everyone", embed=embed)


client.run(TOKEN)
