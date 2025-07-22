import discord
from discord.ext import commands
from config import allowed_roles

def setup_commands(bot: commands.Bot):
    @bot.tree.command(
        name='mensagem',
        description='Envia uma mensagem privada para um usuário'
    )
    @discord.app_commands.describe(
        usuário = 'Usuário a ser enviada a mensagem',
        mensagem = 'Texto'
    )
    
    @discord.app_commands.checks.has_any_role(*allowed_roles)
    async def mensagem(
        interaction: discord.Interaction,
        usuário: discord.User,
        mensagem: str
    ):
        await interaction.response.defer()
        try:
            await usuário.send(mensagem)
            await interaction.followup.send(f"✅ Mensagem enviada com sucesso para **{usuário.name}**.")
        except discord.Forbidden:
            await interaction.followup.send(f"❌ Falha ao enviar a mensagem. O usuário **{usuário.name}** pode ter desativado o recebimento de mensagens privadas.")
        except Exception as e:
            await interaction.followup.send(f"⚠️ Ocorreu um erro inesperado: {e}")
