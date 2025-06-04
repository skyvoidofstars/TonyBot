import discord
from discord.ext import commands
from db import _new_session, Log
from datetime import datetime
from utils.UserManager import has_user_admin_permission
from config import brasilia_tz, LogChannel, MentionID


def setup_commands(bot: commands.Bot):
    @bot.command(
        name="apagar", description="Apaga a mensagem mencionada e a própria do comando."
    )
    async def apagar(ctx: commands.Context):
        if not has_user_admin_permission(discord_uer=ctx.author):
            return
        try:
            if ctx.message.reference:
                message = await ctx.channel.fetch_message(
                    ctx.message.reference.message_id
                )
                log = Log(
                    guild=ctx.guild.name,
                    user_id=ctx.author.id,
                    description=f'Mensagem apagada: {message.id} usado por {ctx.author.name}:\n{message.author.name}: "{message.content}"',
                    timestamp=datetime.now(brasilia_tz),
                )
                session = _new_session()
                session.add(log)
                session.commit()
                session.close()
                await message.delete()
        except Exception as e:
            await bot.get_guild(ctx.guild.id).get_channel(LogChannel).send(
                f"<@{MentionID}>\nErro no comando apagar por {ctx.author.name}:\n{e}"
            )
        finally:
            await ctx.message.delete()
