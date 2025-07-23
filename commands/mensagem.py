import discord
from discord.ext import commands
from config import allowed_roles
from views.mensagem.mensagem import SupervisionMessageModal

def setup_commands(bot: commands.Bot):
    @bot.tree.command(
        name='mensagem',
        description='Envia uma mensagem privada para um usuário'
    )
    @discord.app_commands.describe(
        usuário = 'Usuário a ser enviada a mensagem'
    )
    
    @discord.app_commands.checks.has_any_role(*allowed_roles)
    async def mensagem(
        interaction: discord.Interaction,
        usuário: discord.User
    ):
        await interaction.response.send_modal(SupervisionMessageModal(bot=bot, user=usuário))
