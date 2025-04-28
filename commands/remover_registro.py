import discord
from discord.ext import commands
from config import *
from db import NewSession, Chest
from views.ConfirmRemoveView import ConfirmRemoveView
from datetime import datetime

def setup_commands(bot:commands.Bot):
    @bot.tree.command(name='remover_registro', description='Remove um registro do baú')
    @discord.app_commands.describe(id='ID do registro a ser removido')
    async def remover_registro(interaction:discord.Interaction, id:int):
        try:
            if not any(role.id in AllowedRoles for role in interaction.user.roles):
                await interaction.response.send_message('Você não tem permissão para remover registros!', ephemeral=True)
                return

            session = NewSession()
            chest = session.query(Chest).filter_by(id=id).first()

            if not chest:
                await interaction.response.send_message(f'ID `{id}` não encontrado!', ephemeral=True)
                session.close()
                return

            embed = discord.Embed(
                title='❌ Confirmação de remoção!',
                color=discord.Color.red(),
                timestamp=datetime.now(brasilia_tz)
            )

            embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
            embed.add_field(name='👤 Funcionário', value=f'```\n{chest.getUser.user_character_name.ljust(embed_width)}\n```', inline=False)
            embed.add_field(name='📦 Item', value=f'```\n{chest.item}\n```', inline=True)
            embed.add_field(name='🔢 Quantidade', value=f'```\n{abs(chest.quantity) if chest.item != 'Dinheiro' else '$ ' + str(abs(chest.quantity))}\n```', inline=True)

            await interaction.response.send_message(embed=embed, view=ConfirmRemoveView(session=session, chest=chest, user=interaction.user, bot=bot, entry=chest))
        except Exception as error:
            await interaction.response.send_message(f'Erro genérico!\n{error}', ephemeral=True)
        finally:
            session.close()
        