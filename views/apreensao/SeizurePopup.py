import discord, regex
from discord import ui
from discord.ext import commands
from sqlalchemy.orm import Session
from datetime import datetime
from config import brasilia_tz
from db import User, Seizure, _new_session
from utils.UserManager import get_or_create_user
from utils.ErrorReporting import log_and_notify


def _regex_extraction(pattern: str, value: str) -> str:
    _match = regex.search(pattern, value)
    return _match.group(0) if _match else ''


class SeizureView(ui.Modal, title='🚗 Nova apreensão'):
    officer_name: ui.TextInput = ui.TextInput(
        label='👮 Nome do oficial',
        placeholder='Fulano da Silva',
        required=True,
        style=discord.TextStyle.short,
        max_length=60,
    )
    officer_badge: ui.TextInput = ui.TextInput(
        label='⭐ Nº do distintivo',
        placeholder='012',
        required=True,
        style=discord.TextStyle.short,
        max_length=3,
    )
    observations: ui.TextInput = ui.TextInput(
        label='📝 Observações (opcional)',
        placeholder='Ex: veículo levado pelo seguro, anexado imagem do chamado',
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=1000,
    )

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)

        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        _officer_name: str = _regex_extraction(
            pattern=r'([\p{L}\s]+[\p{L}])', value=self.officer_name.value
        ).title()
        _officer_badge: str = _regex_extraction(
            pattern=r'[0-9]+', value=self.officer_badge.value
        ).rjust(3, '0')
        _observations: str = self.observations.value

        if not _officer_name or not _officer_badge:
            await interaction.response.send_message(
                content='Nome do oficial ou distintivo inválidos',
                ephemeral=True,
                delete_after=30,
            )
            return

        session: Session = _new_session()

        _user: User = get_or_create_user(discord_user=interaction.user)

        seizure: Seizure = Seizure(
            user_id=_user.user_id,
            guild_id=interaction.guild.id,
            officer_name=_officer_name,
            officer_badge=_officer_badge,
            created_at=datetime.now(brasilia_tz),
            observations=_observations,
            status='PENDENTE',
        )

        session.add(seizure)
        session.commit()
        session.close()

        await interaction.response.send_message(
            content=f'{interaction.user.mention} para concluir, envie nesse chat a imagem da apreensão!',
            ephemeral=True,
            delete_after=10,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        session: Session = _new_session()
        await log_and_notify(bot=self.bot, interaction=interaction, text=error)
