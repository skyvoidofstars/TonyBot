import discord
from discord import app_commands
from discord.ext import commands
from db import _new_session
from views.apreensao.SeizurePopup import SeizureView

def setup_commands(bot: commands.Bot):
    apreensoes: app_commands.Group = app_commands.Group(name='apreensao', description='Controle de apreensões realizadas pelos mecânicos')

    @apreensoes.command(name='adicionar', description='Adicionar uma nova apreensão')
    async def adicionar(interaction: discord.Interaction):
        await interaction.response.send_modal(SeizureView(bot=bot))
    
    bot.tree.add_command(apreensoes)