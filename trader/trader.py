import discord
from discord.ext import commands
from discord import app_commands
import mysql.connector
from discord.ui import View, Select, Button

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="twoje_haslo",
    database="trader"
)
cursor = db.cursor()

# Tabela użytkowników i inventory musi już istniec
# CREATE TABLE users (id BIGINT PRIMARY KEY);
# CREATE TABLE inventory (user_id BIGINT, item VARCHAR(100));

def get_inventory(user_id):
    cursor.execute("SELECT item FROM inventory WHERE user_id = %s", (user_id,))
    return [item[0] for item in cursor.fetchall()]

def add_item(user_id, item):
    cursor.execute("INSERT INTO inventory (user_id, item) VALUES (%s, %s)", (user_id, item))
    db.commit()

def remove_item(user_id, item):
    cursor.execute("DELETE FROM inventory WHERE user_id = %s AND item = %s LIMIT 1", (user_id, item))
    db.commit()

def get_all_user_ids():
    cursor.execute("SELECT DISTINCT user_id FROM inventory")
    return [row[0] for row in cursor.fetchall()]

class TradeStartView(View):
    def __init__(self, sender):
        super().__init__()
        self.sender = sender
        user_ids = get_all_user_ids()
        options = [discord.SelectOption(label=f"{bot.get_user(uid)}", value=str(uid)) for uid in user_ids if uid != sender.id]
        self.select = Select(placeholder="Wybierz użytkownika do wymiany", options=options)
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        receiver_id = int(self.select.values[0])
        receiver_inventory = get_inventory(receiver_id)
        sender_inventory = get_inventory(self.sender.id)

        await interaction.response.send_message(
            f"Wybierz przedmiot(y) do otrzymania od {bot.get_user(receiver_id).mention}:",
            view=TradeSelectItems(self.sender.id, receiver_id, receiver_inventory, sender_inventory),
            ephemeral=True
        )

class TradeSelectItems(View):
    def __init__(self, sender_id, receiver_id, recv_items, sender_items):
        super().__init__()
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.recv_select = Select(placeholder="Odbierane przedmioty", options=[discord.SelectOption(label=i, value=i) for i in recv_items], min_values=1, max_values=min(5, len(recv_items)))
        self.send_select = Select(placeholder="Twoje przedmioty", options=[discord.SelectOption(label=i, value=i) for i in sender_items], min_values=1, max_values=min(5, len(sender_items)))
        self.recv_select.callback = self.recv_select_cb
        self.send_select.callback = self.send_select_cb
        self.add_item(self.recv_select)
        self.add_item(self.send_select)

    async def recv_select_cb(self, interaction):
        self.recv_items = self.recv_select.values
        await interaction.response.send_message("Wybrane przedmioty do otrzymania. Teraz wybierz swoje.", ephemeral=True)

    async def send_select_cb(self, interaction):
        self.send_items = self.send_select.values
        receiver = bot.get_user(self.receiver_id)
        sender = bot.get_user(self.sender_id)

        msg = await interaction.response.send_message(
            f"{receiver.mention}, {sender.mention} proponuje wymianę:\n🎁 Oferuje: {', '.join(self.send_items)}\n📦 Chce: {', '.join(self.recv_items)}",
            view=ConfirmTradeView(self.sender_id, self.receiver_id, self.send_items, self.recv_items),
            ephemeral=False
        )

class ConfirmTradeView(View):
    def __init__(self, sender_id, receiver_id, sender_items, receiver_items):
        super().__init__()
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.sender_items = sender_items
        self.receiver_items = receiver_items

    @discord.ui.button(label="✅ Akceptuj", style=discord.ButtonStyle.success)
    async def accept(self, interaction, button):
        if interaction.user.id != self.receiver_id:
            await interaction.response.send_message("Tylko adresat może zaakceptować.", ephemeral=True)
            return
        for item in self.sender_items:
            remove_item(self.sender_id, item)
            add_item(self.receiver_id, item)
        for item in self.receiver_items:
            remove_item(self.receiver_id, item)
            add_item(self.sender_id, item)
        await interaction.response.edit_message(content="✅ Wymiana zakończona sukcesem!", view=None)

    @discord.ui.button(label="❌ Odrzuć", style=discord.ButtonStyle.danger)
    async def decline(self, interaction, button):
        if interaction.user.id != self.receiver_id:
            await interaction.response.send_message("Tylko adresat może odrzucić.", ephemeral=True)
            return
        await interaction.response.edit_message(content="❌ Wymiana została odrzucona.", view=None)

@tree.command(name="trade", description="Rozpocznij wymianę z innym graczem")
async def trade(interaction: discord.Interaction):
    await interaction.response.send_message("Wybierz osobę, z którą chcesz się wymienić:", view=TradeStartView(interaction.user), ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Zalogowano jako {bot.user}")

bot.run("TWÓJ_TOKEN")
