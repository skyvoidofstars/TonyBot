import discord
from discord.ext import commands
from config import *
from utils.UserManager import has_user_admin_permission


def setup_commands(bot: commands.Bot):
    @bot.command(name="echo", description="Envia mensagem.")
    async def echo(ctx: commands.Context, *, message: str):
        if not has_user_admin_permission(discord_uer=ctx.author):
            return

        await ctx.message.delete()

        if ctx.message.reference:
            replied_message = await ctx.channel.fetch_message(
                ctx.message.reference.message_id
            )
            await ctx.send(content=message, reference=replied_message)
        else:
            await ctx.send(content=message)
