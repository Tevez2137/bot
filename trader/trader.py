import discord
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

def save_user(user_id, username):
    cursor = _db.cursor()
    cursor.execute("INSERT IGNORE INTO users (user_id, username) VALUES (%s, %s)", (user_id, username))
    _db.commit()
    cursor.close()


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
            requester_items = get_inventory(self.requester.id)
            target_items = get_inventory(target_id)
            embed = discord.Embed(title="Wymiana", description=f"{self.requester.mention} chce wymienić się z <@{target_id}>")
            embed.add_field(name="Twoje przedmioty", value="\n".join(requester_items) or "Brak")
            embed.add_field(name="Ich przedmioty", value="\n".join(target_items) or "Brak")
            await interaction.response.edit_message(content="Podsumowanie wymiany:", embed=embed, view=None)

class SellStartView(discord.ui.View):
    def __init__(self, requester):
        super().__init__(timeout=60)
        self.requester = requester
        self.add_item(SelectItem(requester))

class SelectItem(discord.ui.Select):
    def __init__(self, requester):
        self.requester = requester
        items = get_inventory(requester.id)

        if not items:
            options = [discord.SelectOption(label="Brak przedmiotów", value="none", default=True)]
        else:
            options = [discord.SelectOption(label=item, value=item) for item in items]

        super().__init__(placeholder="Wybierz przedmiot do sprzedaży", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("Nie masz żadnych przedmiotów do sprzedaży.", ephemeral=True)
            return

        selected_item = self.values[0]
        embed = discord.Embed(
            title="🛒 Sprzedaż przedmiotu",
            description=f"{self.requester.mention} wystawił na sprzedaż: **{selected_item}**",
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(content="Podsumowanie sprzedaży:", embed=embed, view=None)