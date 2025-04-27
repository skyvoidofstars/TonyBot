import discord
from discord.ext import commands
from config import *

def setup_commands(bot: commands.Bot):
    @bot.command(name='echo', description='Envia mensagem.')
    async def echo(ctx:discord.ext.commands.Context, *, message:str):
        if not any(role.id in AllowedRoles for role in ctx.author.roles):
            return
        msg = await ctx.fetch_message(ctx.message.id)
        await msg.delete()
        await ctx.send(message)
        print(f'Mensagem enviada: "{message}" por {ctx.author.name}')