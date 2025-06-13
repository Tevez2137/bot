import discord
from discord.ext import commands
from discord import app_commands
import mysql.connector
from discord.ui import View, Select, Button
from trader.trader import trader
import db.database

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

if __name__ == '__main__':
    polacz("mysql://root:ixltAmoiTlhxCSfcllrbENEtUyawnhhS@mysql.railway.internal:3306/railway", "root", "ixltAmoiTlhxCSfcllrbENEtUyawnhhS", "bocik")
    trader()