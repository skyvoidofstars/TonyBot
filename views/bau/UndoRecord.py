import discord
from discord import ui
from discord.ext import commands
from sqlalchemy.orm import Session
from datetime import datetime
from db import Chest, _new_session
from utils.UserManager import has_user_admin_permission
from config import LogChannel, ChestAllowedChannels


def _is_user_allowed(user: discord.User, chest: Chest) -> bool:
    if user.id != chest.user_id and not has_user_admin_permission(user):
        return False
    return True


class UndoRecordView(ui.View):
    def __init__(self, bot: commands.Bot, chest_id: int):
        super().__init__(timeout=10)
        self.bot = bot
        self.session: Session = _new_session()
        self.chest: Chest = (
            self.session.query(Chest).filter(Chest.chest_id == chest_id).first()
        )

    @ui.button(label='Desfazer', style=discord.ButtonStyle.secondary)
    async def desfazer(self, interaction: discord.Interaction, button: ui.Button):
        if not _is_user_allowed(interaction.user, self.chest):
            await interaction.response.send_message(
                'Você não tem permissão para desfazer este registro.', ephemeral=True
            )
            return

        user_character_name: str = self.chest.user.user_character_name
        item_name: str = self.chest.item.item_name
        quantity: int = self.chest.quantity

        self.session.delete(self.chest)
        self.session.commit()
        self.session.close()
        await self.bot.get_channel(LogChannel).send(
            content=f'Registro de {user_character_name} de {quantity} x {item_name} '
            f'desfeito por {interaction.user.mention}')
        embed: discord.Embed = interaction.message.embeds[0]
        embed.color = discord.Color.light_gray()
        embed.set_field_at(index=3, name='🏷️ Em estoque', value='```-X-```')

        await interaction.message.edit(
            content=f'Registro desfeito por {interaction.user.mention} <t:{int(datetime.now().timestamp())}:R>',
            embed=embed,
            view=None,
        )

        self.stop()

    async def on_timeout(self):
        original_message: discord.Message = await self.bot.get_channel(
            ChestAllowedChannels[0]
        ).fetch_message(self.chest.message_id)

        embed: list[discord.Embed] = original_message.embeds[0]

        await original_message.edit(embed=embed, view=None)
        self.stop()

        return await super().on_timeout()
