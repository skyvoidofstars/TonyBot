import discord
from config import *
from datetime import datetime
from git import Repo

def get_latest_commit_info(repo_path="."):
    repo = Repo(repo_path)
    commit = repo.head.commit
    return commit.hexsha[:7], commit.message.strip()

def setup_events(bot:discord.ext.commands.Bot):
    @bot.event
    async def on_ready():
        sincs = await bot.tree.sync()
        commit_hash, commit_msg = get_latest_commit_info()
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {len(sincs)} comandos sincronizados')
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Bot conectado como {bot.user}')
        await bot.get_guild(LogGuild).get_channel(LogChannel).send(f'<@129620949090697216>\nBot (re)inicializado às {datetime.now().strftime("%H:%M:%S")}\n{len(sincs)} comandos sincronizados\n\nÚltimo commit: `{commit_hash}`: {commit_msg}')