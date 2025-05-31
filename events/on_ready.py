import discord
from discord.ext import commands
from config import *
from datetime import datetime
from utils.CommitInfo import get_latest_commit_info
from views.apreensao.NewSeizure import NewSeizureView
from views.apreensao.SeizureCancel import SeizureCancelView

def setup_events(bot: commands.Bot):
    @bot.event
    async def on_ready():
        
        bot.add_view(NewSeizureView(bot=bot))
        bot.add_view(SeizureCancelView(bot=bot))
        
        sincs = await bot.tree.sync()
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {len(sincs)} comandos sincronizados')
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Bot conectado como {bot.user}')
        
        commit_hash, commit_msg, commit_author, commit_summary = get_latest_commit_info()
        message_content: str = (
            f'Bot (re)inicializado às {datetime.now().strftime("%H:%M:%S")}\n'
            f'{len(sincs)} comandos sincronizados\n\n'
            f'Último commit: `{commit_hash}`.\n'
            f'## {commit_msg.split('\n', 1)[0]}\n'
            f'{commit_msg.split('\n', 1)[1] if len(commit_msg.split('\n', 1)) > 1 else ""}\n'
            f'{commit_summary}\n'
            f'||<@{MentionID}>||'
        )
        for guild in bot.guilds:
            await bot.get_guild(guild.id).get_channel(LogChannel).send(message_content)