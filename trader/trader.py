

traderDescription = "Chętnie się z Tobą czymś wymienie lub pomogę przy wymianie z innym użytkownikiem"

trader = commands.Bot(command_prefix="/", intents=intents, description=traderDescription)

@trader.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@trader.event
async def on_message(message):
    if message.channel.name == "trader" and message.content.lower() == "rozpocznij":
        view = classes.StartTradeView()
        await message.channel.send("🔁 Kliknij, aby rozpocząć wymianę!", view=view)


