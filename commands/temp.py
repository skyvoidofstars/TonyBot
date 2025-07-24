import discord
from discord.ext import commands
from config import allowed_roles
from views.mensagem.mensagem import SupervisionMessageModal

def setup_commands(bot: commands.Bot):
    @bot.tree.command(
        name='temp',
        description='temp'
    )    
    @discord.app_commands.checks.has_any_role(*allowed_roles)
    async def temp(
        interaction: discord.Interaction
    ):
        mensagem: discord.Message = await bot.get_channel(1380285028722016346).fetch_message(1397033174235877386)
        embed: discord.Embed = mensagem.embeds[0]
        embed.title = 'Reembolso de apreensões (05/06 à 20/07)'
        await mensagem.edit(content=mensagem.content, embed=embed)