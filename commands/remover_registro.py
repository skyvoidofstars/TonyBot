import discord
from discord.ext import commands
from config import *
from db import NewSession, Chest
from views.ConfirmRemoveView import ConfirmRemoveView
from datetime import datetime

def setup_commands(bot:commands.Bot):
    @bot.tree.command(name='remover_registro', description='Remove um registro do baú')
    @discord.app_commands.checks.has_any_role(*AllowedRoles)
    @discord.app_commands.describe(id='ID do registro a ser removido')
    async def remover_registro(interaction:discord.Interaction, id:int):

        session = NewSession()
        chest = session.query(Chest).filter_by(chest_id=id).first()

        if not chest:
            await interaction.response.send_message(f'ID `{id}` não encontrado!', ephemeral=True)
            return

        embed = discord.Embed(
            title='❌ Confirmação de remoção!',
            color=discord.Color.red(),
            timestamp=datetime.now(brasilia_tz)
        )

        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name='👤 Funcionário', value=f'```\n{chest.user.user_character_name.ljust(embed_width)}\n```', inline=False)
        embed.add_field(name='📦 Item', value=f'```\n{chest.item.item_name}\n```', inline=True)
        embed.add_field(name='🔢 Quantidade', value=f'```\n{chest.quantity if chest.item.item_name != 'Dinheiro' else '$ ' + str(chest.quantity)}\n```', inline=True)

        await interaction.response.send_message(embed=embed, view=ConfirmRemoveView(session=session, chest=chest, interaction=interaction, bot=bot))
        session.close()
        