import discord
from discord import ui
from discord.ext import commands
from .SeizurePopup import SeizureView

class NewSeizureView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.custom_id = "new_seizure_persistent_button"
    
    @ui.button(label="Nova Apreensão", style=discord.ButtonStyle.success, custom_id="new_seizure_button")
    async def new_seizure_button(self, interaction: discord.Interaction, button: ui.Button):
        modal = SeizureView(bot=self.bot)

        await interaction.response.send_modal(modal)