import discord
from discord import ui
from discord.ext import commands
from datetime import datetime

# def _new_embed():
#     1=1

class ApproveRefundView(ui.View):
    def __init__(self, bot: commands.Bot, original_message: discord.Message, limit_date: datetime):
        super().__init__(timeout=90)
        self.bot = bot
        self.original_message = original_message
        self.limit_date = limit_date

    @ui.button(label='Confirmar reembolsos', style=discord.ButtonStyle.success)
    async def approve_button(self, interaction: discord.Interaction, button: ui.Button):
        self.original_message = interaction.message
    
    async def on_timeout(self):
        await self.original_message.edit(content=self.original_message.content, view=None)
        self.stop()