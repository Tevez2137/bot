import discord
from discord.ext import commands
import os
import trader.trader as trader

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

db_config = {
    'host': os.environ.get("MYSQLHOST"),
    'user': os.environ.get("MYSQLUSER"),
    'password': os.environ.get("MYSQLPASSWORD"),
    'database': os.environ.get("MYSQL_DATABASE")
}

@tree.command(name="trade", description="Rozpocznij wymianę z innym graczem")
async def trade(interaction: discord.Interaction):
    await interaction.response.send_message("Wybierz osobę, z którą chcesz się wymienić:", view=trader.TradeStartView(interaction.user), ephemeral=True)

@tree.command(name="sell", description="Rozpocznij sprzedaż:")
async def sell(interaction: discord.Interaction):
    await interaction.response.send_message("Wybierz przedmiot który chcesz sprzedać:", view=trader.SellStartView(interaction.user), ephemeral=True)

@tree.command(name="buy", description="Co chcesz kupić:")
async def sell(interaction: discord.Interaction):
    await interaction.response.send_message("Wybierz przedmiot który chcesz kupić:", view=trader.BuyStartView(interaction.user), ephemeral=True)


@bot.event
async def on_ready():
    trader.setup_db(db_config)
    await tree.sync()
    print(f"Zalogowano jako {bot.user}")
    for guild in bot.guilds:
        for member in guild.members:
            if member.bot:
                continue
            trader.save_user(member.id, member.display_name)

@bot.event
async def on_member_join(member):
    if not member.bot:
        trader.save_user(member.id, member.display_name)


bot.run(os.environ.get("TOKEN"))
