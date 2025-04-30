import discord
from discord.ext import commands
from config import *

def setup_commands(bot: commands.Bot):
    @bot.command(name='apagar', description='Apaga a mensagem mencionada e a própria do comando.')
    async def apagar(ctx:discord.ext.commands.Context, id:int):
        await ctx.message.delete()
        if not any(role.id in AllowedRoles for role in ctx.author.roles):
            return
        if id:
            try:
                msg = await ctx.channel.fetch_message(id)
                await bot.get_guild(LogGuild).get_channel(LogChannel).send(f'Mensagem apagada: {id} por {ctx.author.name}\n\n{msg.author.name}:\n"{msg.content}"')
                await msg.delete()
            except Exception as e:
                await bot.get_guild(LogGuild).get_channel(LogChannel).send(f'<@129620949090697216>\nErro no comando apagar por {ctx.author.name}:\n{e}')
