import discord
from discord.ext import commands
from db import NewSession, User
from config import *

def setup_commands(bot:commands.Bot):
    @bot.tree.command(name='nome', description='Altera o nome de um personagem')
    @discord.app_commands.checks.has_any_role(*AllowedRoles)
    async def nome(interaction:discord.Interaction, usuário:discord.User, nome:str):
        session = NewSession()
        user = session.query(User).filter_by(user_id=usuário.id).first()
        if not user:
            session.close()
            await interaction.response.send_message(f'{usuário.mention} não está cadastrado no banco de dados!', ephemeral=True, delete_after=5)
            return
        user.user_character_name = nome
        session.commit()
        session.close()
        await interaction.response.send_message(f'Nome de {usuário.mention} alterado para `{nome}` com sucesso!', ephemeral=True, delete_after=5)