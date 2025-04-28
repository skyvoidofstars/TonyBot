import discord
from discord.ext import commands
from datetime import datetime
from config import *

class NewBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=command_prefix,
            intents=discord.Intents.all()
        )

    async def setup_hook(self):
        sincs = await self.tree.sync()
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {len(sincs)} comandos sincronizados')

    async def on_ready(self):
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Bot conectado como {self.user}')
        await self.get_guild(LogGuild).get_channel(LogChannel).send(f'<@129620949090697216>\nBot inicializado às {datetime.now().strftime("%H:%M:%S")}')