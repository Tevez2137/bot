import discord
import discord.ext.commands as commands
import trader.classes as classes
import trader.trader
if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    trader.run()