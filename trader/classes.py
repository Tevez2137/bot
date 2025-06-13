class StartTradeView(discord.ui.View):
    @discord.ui.button(label="🔁 Rozpocznij wymianę", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_ids = get_all_user_ids_with_inventory()  # np. z JSON-a
        options = [discord.SelectOption(label=user_name_from_id(uid), value=uid) for uid in user_ids if uid != str(interaction.user.id)]
        await interaction.response.send_message("🔎 Wybierz użytkownika do wymiany:", view=UserSelectView(options), ephemeral=True)


class UserSelectView(discord.ui.View):
    def __init__(self, options):
        super().__init__()
        self.add_item(TradeUserSelect(options))


class TradeUserSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Wybierz użytkownika...", options=options)

    async def callback(self, interaction: discord.Interaction):
        target_user_id = self.values[0]
        inventory = get_inventory(target_user_id)
        options = [discord.SelectOption(label=item, value=item) for item in inventory]
        await interaction.response.send_message(f"🎁 Co chcesz od niego?", view=ItemSelectView(options), ephemeral=True)
