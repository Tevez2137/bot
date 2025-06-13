import discord
from discord.ext import commands
from discord import app_commands
import os
from trader.trader import TradeStartView, setup_db

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

db_config = {
    'host': os.environ.get("MYSQLHOST"),
    'user': os.environ.get("MYSQLUSER"),
    'password': os.environ.get("MYSQLPASSWORD"),
    'database': os.environ.get("MYSQL_DATABASE")
}

@tree.command(name="trade", description="Rozpocznij wymianę z innym graczem")
async def trade(interaction: discord.Interaction):
    await interaction.response.send_message("Wybierz osobę, z którą chcesz się wymienić:", view=TradeStartView(interaction.user), ephemeral=True)

@bot.event
async def on_ready():
    setup_db(db_config)
    await tree.sync()
    print(f"Zalogowano jako {bot.user}")

bot.run(os.environ.get("TOKEN"))
