import discord
from discord.ext import commands
from discord import app_commands
import mysql
from discord.ui import View, Select, Button
from trader.trader import trader


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

if __name__ == '__main__':
    db = mysql.connector.connect(
        host="mysql://root:ixltAmoiTlhxCSfcllrbENEtUyawnhhS@mysql.railway.internal:3306/railway",
        user="root",
        password="ixltAmoiTlhxCSfcllrbENEtUyawnhhS",
        database=
    )
    cursor = db.cursor()
    trader(cursor)