import discord
from discord import ui
from discord.ext import commands
from sqlalchemy.orm import Session
from datetime import datetime
from db import Seizure, Log, _new_session
from config import brasilia_tz, LogChannel
from utils.UserManager import has_user_admin_permission


def _is_user_allowed(user: discord.User, seizure: Seizure) -> bool:
    if user.id != seizure.user_id and not has_user_admin_permission(user):
        return False
    return True


class SeizureCancelView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot: commands.Bot = bot
        self.custom_id: str = "seizure_cancel_persistent_view"

    @ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.danger,
        custom_id="cancel_seizure_button",
    )
    async def cancel_seizure_button_callback(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        session: Session = _new_session()
        seizure: Seizure | None = (
            session.query(Seizure).filter_by(message_id=interaction.message.id).first()
        )

        if not _is_user_allowed(user=interaction.user, seizure=seizure):
            await interaction.response.send_message(
                "Você não tem permissão para cancelar esta apreensão.", ephemeral=True
            )
            session.close()
            return

        seizure.status = "CANCELADO"
        session.add(seizure)
        session.commit()

        log = Log(
            guild=interaction.guild_id,
            user_id=interaction.user.id,
            description=f"Apreensão ID {seizure.seizure_id} (Oficial: {seizure.officer_name} #{seizure.officer_badge}) de {seizure.user.user_character_name} foi CANCELADA por {interaction.user.name}.",
            timestamp=datetime.now(brasilia_tz),
        )
        session.add(log)
        session.commit()
        session.refresh(log)

        await self.bot.get_guild(int(log.guild)).get_channel(LogChannel).send(
            content=log.description
        )

        session.close()

        for item in self.children:
            if isinstance(item, ui.Button):
                item.disabled = True

        original_embed = interaction.message.embeds[0]
        original_embed.color = discord.Color.dark_red()
        await interaction.response.edit_message(
            content=f"Apreensão cancelada por {interaction.user.mention} <t:{int(datetime.now().timestamp())}:R>.",
            embed=original_embed,
            view=None,
        )

        self.stop()
