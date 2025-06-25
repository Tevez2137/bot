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

def save_user(user_id, username):
    cursor = _db.cursor()
    cursor.execute("INSERT IGNORE INTO users (id, login) VALUES (%s, %s)", (user_id, username))
    _db.commit()
    cursor.close()

def get_inventory(user_id):
    cursor = _db.cursor()
    cursor.execute("SELECT item FROM inventory WHERE user_id = %s", (user_id,))
    items = cursor.fetchall()
    cursor.close()
    return [item[0] for item in items]

class TradeStartView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=60)
        self.add_item(SelectUser(interaction))

class SelectUser(discord.ui.Select):
    def __init__(self, interaction: discord.Interaction):
        requester = interaction.user
        members = interaction.guild.members
        options = [
            discord.SelectOption(label=member.display_name, value=str(member.id))
            for member in members if member != requester and not member.bot
        ]
        super().__init__(placeholder="Wybierz użytkownika", min_values=1, max_values=1, options=options)
        self.interaction = interaction
        self.requester = requester

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        target_id = int(self.values[0])
        target_user = interaction.guild.get_member(target_id)

        requester_items = get_inventory(self.requester.id)
        target_items = get_inventory(target_id)

        embed = discord.Embed(
            title="Wymiana",
            description=f"{self.requester.mention} chce wymienić się z {target_user.mention}"
        )
        embed.add_field(name="Twoje przedmioty", value="\n".join(requester_items) or "Brak")
        embed.add_field(name="Ich przedmioty", value="\n".join(target_items) or "Brak")

        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            content="Wybierz przedmioty do wymiany:",
            embed=embed,
            view=TradeSessionView(self.requester, target_user, requester_items, target_items)
        )

class TradeSessionView(discord.ui.View):
    def __init__(self, requester, target_user, requester_items, target_items):
        super().__init__(timeout=120)
        self.requester = requester
        self.target_user = target_user
        self.requester_items = requester_items
        self.target_items = target_items
        self.selected_requester_items = requester_items[:1]  # przykładowo wybiera 1 na sztywno
        self.selected_target_items = target_items[:1]
        self.add_item(ConfirmTradeButton(self))

class ConfirmTradeButton(discord.ui.Button):
    def __init__(self, trade_view):
        super().__init__(label="Zatwierdź wymianę", style=discord.ButtonStyle.green)
        self.trade_view = trade_view

    async def callback(self, interaction: discord.Interaction):
        requester_id = self.view.requester.id
        target_id = self.view.target_user.id

        cursor = _db.cursor()

        for item in self.view.selected_requester_items:
            cursor.execute("UPDATE inventory SET user_id = %s WHERE item = %s AND user_id = %s", (target_id, item, requester_id))

        for item in self.view.selected_target_items:
            cursor.execute("UPDATE inventory SET user_id = %s WHERE item = %s AND user_id = %s", (requester_id, item, target_id))

        _db.commit()
        cursor.close()

        await interaction.response.send_message("✅ Wymiana zakończona pomyślnie!", ephemeral=True)
        self.view.stop()