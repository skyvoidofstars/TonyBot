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
        if ctx.message.reference:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            await ctx.send(message, reference=replied_message)
        else:
            await ctx.send(message)