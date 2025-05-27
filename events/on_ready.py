import discord
from config import *
from datetime import datetime
from git import Repo

def get_latest_commit_info(repo_path="."):
    repo = Repo(repo_path)
    commit = repo.head.commit
    
    diff = commit.diff(commit.parents[0])

    lines = []

    for item in diff.iter_change_type('D'):
        lines.append(f"\u001b[2;32m\u001b[1;32m+ {item.b_path}\u001b[0m")
    for item in diff.iter_change_type('M'):
        lines.append(f"\u001b[2;33m\u001b[1;33m± {item.b_path}\u001b[0m")
    for item in diff.iter_change_type('A'):
        lines.append(f"\u001b[2;31m\u001b[1;31m- {item.a_path}\u001b[0m")

    commit_summary = "```ansi\n" + "\n".join(lines) + "\n```"
    
    return commit.hexsha[:10], commit.message.strip(), commit.author.name, commit_summary

def setup_events(bot:discord.ext.commands.Bot):
    @bot.event
    async def on_ready():
        sincs = await bot.tree.sync()
        commit_hash, commit_msg, commit_author, commit_summary = get_latest_commit_info()
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {len(sincs)} comandos sincronizados')
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Bot conectado como {bot.user}')
        await bot.get_guild(LogGuild).get_channel(LogChannel).send(f'Bot (re)inicializado às {datetime.now().strftime("%H:%M:%S")}\n{len(sincs)} comandos sincronizados\n\nÚltimo commit: `{commit_hash}` por {commit_author}.\n\n{commit_msg}\n{commit_summary}\n||<@{MentionID}>||')