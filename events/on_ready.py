import discord
from config import *
from datetime import datetime
from utils.commit_info import get_latest_commit_info

def setup_events(bot:discord.ext.commands.Bot):
    @bot.event
    async def on_ready():
        sincs = await bot.tree.sync()
        commit_hash, commit_msg, commit_author, commit_summary = get_latest_commit_info()
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {len(sincs)} comandos sincronizados')
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Bot conectado como {bot.user}')
        
        message_content: str = (
            f'Bot (re)inicializado às {datetime.now().strftime("%H:%M:%S")}\n'
            f'{len(sincs)} comandos sincronizados\n\n'
            f'Último commit: `{commit_hash}`.\n\n'
            f'## {commit_msg.split('\n', 1)[0]}\n'
            f'{commit_msg.split('\n', 1)[1] if len(commit_msg.split('\n', 1)) > 1 else ""}\n'
            f'{commit_summary}\n'
            f'||<@{MentionID}>||'
        )
        
        await bot.get_guild(LogGuild).get_channel(LogChannel).send(message_content)