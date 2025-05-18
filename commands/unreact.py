import discord
from discord.ext import commands
from config import *

def setup_commands(bot:commands.Bot):
    @bot.command(name='unreact', description='Reage a mensagem mencionada.')
    async def unreact(ctx:discord.ext.commands.Context, channel_id:int, message_id:int):
        if not any(role.id in AllowedRoles for role in ctx.author.roles):
            return
        try:
            message = await bot.get_channel(channel_id).fetch_message(message_id)
            for reaction in message.reactions:
                async for user in reaction.users():
                    if user == ctx.me:
                        await message.remove_reaction(reaction.emoji, ctx.me)
        except Exception as e:
            await bot.get_guild(LogGuild).get_channel(LogChannel).send(f'<@{MentionID}>\nErro no comando react por {ctx.author.name}:\n{e}')
        finally:
            await ctx.message.delete()