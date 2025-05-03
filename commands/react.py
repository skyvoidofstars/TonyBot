import discord
from discord.ext import commands
from config import *

def setup_commands(bot:commands.Bot):
    @bot.command(name='react', description='Reage a mensagem mencionada.')
    async def react(ctx:discord.ext.commands.Context, reaction:str):
        if not any(role.id in AllowedRoles for role in ctx.author.roles):
            return
        try:
            if ctx.message.reference:
                message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                await message.add_reaction(reaction)
        except Exception as e:
            await bot.get_guild(LogGuild).get_channel(LogChannel).send(f'<@129620949090697216>\nErro no comando react por {ctx.author.name}:\n{e}')
        finally:
            await ctx.message.delete()