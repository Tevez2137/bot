import discord
from discord.ui import View, Select, Button
import mysql.connector

_db = None

def setup_db(config):
    global _db
    _db = mysql.connector.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )

def get_inventory(user_id):
    cursor = _db.cursor()
    cursor.execute("SELECT item FROM inventory WHERE user_id = %s", (user_id,))
    items = cursor.fetchall()
    cursor.close()
    return [item[0] for item in items]

class TradeStartView(discord.ui.View):
    def __init__(self, requester):
        super().__init__(timeout=60)
        self.requester = requester
        self.add_item(SelectUser(requester))

class SelectUser(discord.ui.Select):
    def __init__(self, requester):
        options = [
            discord.SelectOption(label=member.display_name, value=str(member.id))
            for member in requester.guild.members
            if member != requester and not member.bot
        ]
        super().__init__(placeholder="Wybierz użytkownika", min_values=1, max_values=1, options=options)
        self.requester = requester

    async def callback(self, interaction: discord.Interaction):
        target_id = int(self.values[0])
        target_user = interaction.guild.get_member(target_id)
        requester_items = get_inventory(self.requester.id)
        target_items = get_inventory(target_id)

        embed = discord.Embed(title="Wymiana", description=f"{self.requester.mention} chce wymienić się z {target_user.mention}")
        embed.add_field(name="Twoje przedmioty", value="\n".join(requester_items) or "Brak", inline=True)
        embed.add_field(name=f"Przedmioty {target_user.display_name}", value="\n".join(target_items) or "Brak", inline=True)

        view = TradeSessionView(self.requester, target_user, requester_items, target_items)
        await interaction.response.edit_message(content="Podsumowanie wymiany:", embed=embed, view=view)

class TradeSessionView(discord.ui.View):
    def __init__(self, requester, target_user, requester_items, target_items):
        super().__init__(timeout=120)
        self.requester = requester
        self.target_user = target_user
        self.requester_items = requester_items
        self.target_items = target_items

        self.add_item(ConfirmTradeButton(self))

class ConfirmTradeButton(discord.ui.Button):
    def __init__(self, trade_view):
        super().__init__(label="Potwierdź wymianę", style=discord.ButtonStyle.success)
        self.trade_view = trade_view

    async def callback(self, interaction: discord.Interaction):
        requester = self.trade_view.requester
        target_user = self.trade_view.target_user


        await interaction.response.send_message(
            f"Wymiana zakończona między {requester.mention} a {target_user.mention}!", ephemeral=False
        )
