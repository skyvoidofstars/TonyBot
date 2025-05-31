import discord
from discord.ext import commands
from sqlalchemy.orm import Session
from db import User, Log
from config import LogChannel, MentionID
from utils.UserManager import get_or_create_user

async def log_and_notify(bot: commands.Bot, interaction: discord.Interaction, session: Session, text: str, severity: int = 0) -> None:
    _guild_id: int = interaction.guild.id
    _channel_id: int = interaction.channel.id
    _user: User = get_or_create_user(interaction.user)

    await bot.get_guild(_guild_id).get_channel(_channel_id).send(f'{interaction.user.mention} Erro ao executar o comando {interaction.command.name}!\n\n{text}')

    await bot.get_guild(interaction.guild.id).get_channel(LogChannel).send(f'<@{MentionID}>\nErro no comando {interaction.command.name} por {interaction.user.name}:\n{text}')

    _log: Log = Log(
        guild=_guild_id,
        user_id=_user.user_id,
        description=text,
    )
    session.add(_log)
    session.commit()
    session.close()

    if severity >= 0:
        await bot.get_user().send(
            f'Erro no comando {interaction.command.name}\n'
            f'Usuário: {interaction.user.mention}\n'
            f'Canal: {interaction.channel.mention} ({interaction.channel.name})\n'
            f'Mensagem: {text}'
        )
