import discord
from discord.ext import commands
from config import *

def setup_commands(bot: commands.Bot):
    @bot.command(name='apagar', description='Apaga a mensagem mencionada e a própria do comando.')
    async def apagar(ctx:discord.ext.commands.Context):
        if not any(role.id in AllowedRoles for role in ctx.author.roles):
            return
        try:
            if ctx.message.reference:
                message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                await bot.get_guild(LogGuild).get_channel(LogChannel).send(f'Mensagem apagada: {message.id} usado por {ctx.author.name}:\n{message.author.mention}: "{message.content}"')
                await message.delete()
        except Exception as e:
            await bot.get_guild(LogGuild).get_channel(LogChannel).send(f'<@129620949090697216>\nErro no comando apagar por {ctx.author.name}:\n{e}')
        finally:
            await ctx.message.delete()