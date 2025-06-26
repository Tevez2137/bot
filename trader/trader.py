import discord
from discord.ui import View, Select, Button
import mysql.connector

_db = None

# --- DB setup & helpers ---
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
    return items

# --- Trade Views ---
class TradeStartView(View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=60)
        self.add_item(SelectUser(interaction))

class SelectUser(Select):
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
        await interaction.response.edit_message(
            content="Wybierz przedmioty, które chcesz oddać:",
            view=SelectGiveView(self.requester, int(self.values[0]))
        )

class SelectGiveView(View):
    def __init__(self, requester, target_id):
        super().__init__(timeout=60)
        self.requester = requester
        self.target_id = target_id
        items = get_inventory(requester.id)
        self.add_item(GiveSelect(items, requester, target_id))

class GiveSelect(Select):
    def __init__(self, items, requester, target_id):
        options = [discord.SelectOption(label=item, value=item) for item in items]
        super().__init__(placeholder="Wybierz przedmioty do oddania", min_values=1, max_values=len(options), options=options)
        self.requester = requester
        self.target_id = target_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content="Wybierz przedmioty, które chcesz otrzymać:",
            view=SelectReceiveView(self.requester, self.target_id, self.values)
        )

class SelectReceiveView(View):
    def __init__(self, requester, target_id, give_items):
        super().__init__(timeout=60)
        self.requester = requester
        self.target_id = target_id
        self.give_items = give_items
        items = get_inventory(target_id)
        self.add_item(ReceiveSelect(items, requester, target_id, give_items))

class ReceiveSelect(Select):
    def __init__(self, items, requester, target_id, give_items):
        options = [discord.SelectOption(label=item, value=item) for item in items]
        super().__init__(placeholder="Wybierz przedmioty do otrzymania", min_values=1, max_values=len(options), options=options)
        self.requester = requester
        self.target_id = target_id
        self.give_items = give_items

    async def callback(self, interaction: discord.Interaction):
        target_user = interaction.guild.get_member(self.target_id)
        embed = discord.Embed(title="Propozycja wymiany", description=f"{self.requester.mention} proponuje wymianę:")
        embed.add_field(name="Oddaje", value="\n".join(self.give_items), inline=True)
        embed.add_field(name="Oczekuje", value="\n".join(self.values), inline=True)

        try:
            await target_user.send(
                embed=embed,
                view=ConfirmTradeView(self.requester, target_user, self.give_items, self.values)
            )
            await interaction.response.edit_message(content="✅ Propozycja wymiany została wysłana!", view=None)
        except discord.Forbidden:
            await interaction.response.edit_message(content="❌ Nie można wysłać wiadomości do tego użytkownika.", view=None)

class ConfirmTradeView(View):
    def __init__(self, requester, target_user, give_items, receive_items):
        super().__init__(timeout=120)
        self.requester = requester
        self.target_user = target_user
        self.give_items = give_items
        self.receive_items = receive_items
        self.add_item(ConfirmTradeButton(self))

class ConfirmTradeButton(Button):
    def __init__(self, trade_view):
        super().__init__(label="Akceptuj wymianę", style=discord.ButtonStyle.green)
        self.trade_view = trade_view

    async def callback(self, interaction: discord.Interaction):
        cursor = _db.cursor()
        for item in self.trade_view.give_items:
            cursor.execute("UPDATE inventory SET user_id = %s WHERE item = %s AND user_id = %s",
                           (self.trade_view.target_user.id, item, self.trade_view.requester.id))
        for item in self.trade_view.receive_items:
            cursor.execute("UPDATE inventory SET user_id = %s WHERE item = %s AND user_id = %s",
                           (self.trade_view.requester.id, item, self.trade_view.target_user.id))
        _db.commit()
        cursor.close()

        await interaction.response.send_message("✅ Wymiana zakończona pomyślnie!", ephemeral=True)
        self.trade_view.stop()
