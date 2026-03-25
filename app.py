import discord
from discord import app_commands
from mcstatus import JavaServer
import asyncio
import os

TOKEN = os.getenv("TOKEN")

SERVER = "score-complexity.gl.joinmc.link"
PORT = 25565

CHANNEL_NAME = "downdetector"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

last_status = None
cooldown = False


# 🔹 Fancy embed builder
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
    global last_status, cooldown

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

        if last_status is None:
            last_status = current_status

        if current_status != last_status and not cooldown:
            for guild in client.guilds:
                for channel in guild.text_channels:
                    if channel.name == CHANNEL_NAME:
                        embed = build_embed(current_status, players, max_players, names)

                        if current_status:
                            await channel.send("@everyone", embed=embed)
                        else:
                            await channel.send("@everyone", embed=embed)

            last_status = current_status
            cooldown = True

            # prevent spam
            await asyncio.sleep(60)
            cooldown = False

        await asyncio.sleep(15)


# 🔹 Slash command: /status
@tree.command(name="status", description="Check Minecraft server status")
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


# 🔹 Slash command: /maintenance
@tree.command(name="maintenance", description="Send maintenance announcement")
@app_commands.describe(message="Maintenance message")
async def maintenance(interaction: discord.Interaction, message: str):

    embed = discord.Embed(
        title="🛠️ Maintenance Announcement",
        description=message,
        color=0xf59e0b
    )

    embed.set_footer(text="Server Team")

    await interaction.response.send_message("Announcement sent!", ephemeral=True)

    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.name == CHANNEL_NAME:
                await channel.send("@everyone", embed=embed)


client.run(TOKEN)
