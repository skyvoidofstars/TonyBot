import discord
from discord.ext import commands
from datetime import datetime
from config import *


class NewBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=command_prefix, intents=discord.Intents.all())
