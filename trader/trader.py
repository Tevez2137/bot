import discord
from discord.ext import commands
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
            for member in requester.guild.members if member != requester and not member.bot
        ]
        super().__init__(placeholder="Wybierz użytkownika", min_values=1, max_values=1, options=options)
        self.requester = requester

    async def callback(self, interaction: discord.Interaction):
        target_id = int(self.values[0])
        target_user = interaction.guild.get_member(target_id)

        requester_items = get_inventory(self.requester.id)
        target_items = get_inventory(target_id)

        embed = discord.Embed(title="Wymiana", description=f"{self.requester.mention} chce wymienić się z {target_user.mention}")
        embed.add_field(name="Twoje przedmioty", value="\n".join(requester_items) or "Brak")
        embed.add_field(name="Ich przedmioty", value="\n".join(target_items) or "Brak")

        await interaction.response.edit_message(
            content="Wybierz przedmioty do wymiany:",
            embed=embed,
            view=TradeSessionView(self.requester, target_user, requester_items, target_items)
        )

class TradeSessionView(discord.ui.View):
    def __init__(self, requester, target, requester_items, target_items):
        super().__init__(timeout=300)
        self.requester = requester
        self.target = target
        self.selected_requester_items = []
        self.selected_target_items = []

        self.add_item(SelectTradeItems("Twoje przedmioty", requester_items, self.selected_requester_items))
        self.add_item(SelectTradeItems("Ich przedmioty", target_items, self.selected_target_items))
        self.add_item(ConfirmTradeButton(self))

class SelectTradeItems(discord.ui.Select):
    def __init__(self, placeholder, items, selected_items_storage):
        options = [discord.SelectOption(label=item, value=item) for item in items]
        super().__init__(placeholder=placeholder, min_values=0, max_values=len(items), options=options)
        self.selected_items_storage = selected_items_storage

    async def callback(self, interaction: discord.Interaction):
        self.selected_items_storage.clear()
        self.selected_items_storage.extend(self.values)
        await interaction.response.send_message(f"Wybrane: {', '.join(self.values)}", ephemeral=True)

class ConfirmTradeButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(label="Zatwierdź wymianę", style=discord.ButtonStyle.green)
        self.view = view

    async def callback(self, interaction: discord.Interaction):
        requester_id = self.view.requester.id
        target_id = self.view.target.id

        cursor = _db.cursor()

        for item in self.view.selected_requester_items:
            cursor.execute("UPDATE inventory SET user_id = %s WHERE item = %s AND user_id = %s", (target_id, item, requester_id))

        for item in self.view.selected_target_items:
            cursor.execute("UPDATE inventory SET user_id = %s WHERE item = %s AND user_id = %s", (requester_id, item, target_id))

        _db.commit()
        cursor.close()

        await interaction.response.send_message("✅ Wymiana zakończona pomyślnie!", ephemeral=True)
        self.view.stop()
