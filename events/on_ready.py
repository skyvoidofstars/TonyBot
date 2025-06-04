import discord, time
from discord.ext import commands
from config import *
from datetime import datetime
from sqlalchemy.orm import Session
from db import SeizureRefund, _new_session
from utils.CommitInfo import get_latest_commit_info
from utils.PersistantViewManager import update_new_seizure_message
from utils.ANSI import Colors
from views.apreensao.NewSeizure import NewSeizureView
from views.apreensao.SeizureCancel import SeizureCancelView
from views.apreensao.RefundButtons import RefundButtonsView


def _add_views(bot: commands.Bot):
    bot.add_view(NewSeizureView(bot=bot))
    bot.add_view(SeizureCancelView(bot=bot))
    bot.add_view(RefundButtonsView(bot=bot))


def setup_events(bot: commands.Bot):
    @bot.event
    async def on_ready():
        await update_new_seizure_message(bot=bot)

        _add_views(bot=bot)

        syncs = await bot.tree.sync()
        print(
            f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {len(syncs)} comandos sincronizados\n'
            f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Bot conectado como {bot.user} em {len(bot.guilds)} servidor{'es' if len(bot.guilds) > 1 else ''}!'
        )

        commit_hash, commit_msg, commit_summary = get_latest_commit_info()
        message_content: str = (
            f'Bot (re)inicializado às {datetime.now().strftime("%H:%M:%S")}\n'
            f"{len(syncs)} comandos sincronizados\n\n"
            f"Último commit: `{commit_hash}`.\n"
            f'## {commit_msg.split('\n', 1)[0]}\n'
            f'{commit_msg.split('\n', 1)[1] if len(commit_msg.split('\n', 1)) > 1 else ""}\n'
            f"{commit_summary}\n"
            f"||<@{MentionID}>||"
        )
        for guild in bot.guilds:
            await bot.get_guild(guild.id).get_channel(LogChannel).send(message_content)
