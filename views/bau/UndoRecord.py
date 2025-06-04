import discord, regex
from discord import ui
from discord.ext import commands
from sqlalchemy.orm import Session
from datetime import datetime
from db import Chest
from utils.UserManager import has_user_admin_permission
from config import LogChannel, ChestAllowedChannels

# def _get_chest_id(interaction: discord.Interaction) -> int:
#     _pattern: str = r'[0-9]+'
#     _string: str = interaction.message.embeds[0].footer.text
#     _match_str: str = regex.search(string=_string, pattern=_pattern).group(0)
#     _chest_id: int = int(_match_str)

#     return _chest_id
def _is_user_allowed(user: discord.User, chest: Chest) -> bool:
    if user.id != chest.user_id and not has_user_admin_permission(user):
        return False
    return True

class UndoRecordView(ui.View):
    def __init__(self, bot: commands.Bot, chest: Chest, session: Session):
        super().__init__(timeout=15)
        self.bot = bot
        self.chest = chest
        self.session = session

    @ui.button(label="Desfazer", style=discord.ButtonStyle.secondary, emoji="📦")
    async def desfazer(self, interaction: discord.Interaction, button: ui.Button):
        if not _is_user_allowed(interaction.user, self.chest):
            await interaction.response.send_message("Você não tem permissão para desfazer este registro.", ephemeral=True)
            return
        
        self.session.delete(self.chest)
        self.session.commit()
        self.session.close()
        await self.bot.get_channel(LogChannel).send(
            content = f'Registro de {self.chest.user.user_character_name} de {self.chest.quantity} x {self.chest.item.item_name}' \
            f'desfeito por {interaction.user.mention}'
        )

        embed: discord.Embed = interaction.message.embeds[0]
        embed.color = discord.Color.light_gray()

        await interaction.message.edit(
            content = f'Registro desfeito por {interaction.user.mention} <t:{int(datetime.now().timestamp())}:R>',
            embed = embed,
            view = None
        )

        self.stop()

    async def on_timeout(self):
        message: discord.Message = await self.bot.get_channel(ChestAllowedChannels[0]).fetch_message(self.chest.message_id)

        await message.edit(embeds=message.embeds, view=None)
        self.stop()
        
        return await super().on_timeout()
    