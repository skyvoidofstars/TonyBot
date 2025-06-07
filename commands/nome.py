import discord
from discord.ext import commands
from config import allowed_roles
from sqlalchemy.orm import Session
from db import _new_session, User
from utils.UserManager import get_or_create_user


def setup_commands(bot: commands.Bot):
    @bot.tree.command(name='nome', description='Altera o nome do personagem de um usuário')
    @discord.app_commands.checks.has_any_role(*allowed_roles)
    @discord.app_commands.describe(
        usuário='Usuário a ter o nome alterado',
        nome_sobrenome='Nome e Sobrenome do personagem'
    )
    async def nome(
        interaction: discord.Interaction,
        usuário: discord.User,
        nome_sobrenome: str
    ):
        session: Session = _new_session()
        
        user: User = get_or_create_user(usuário)
        old_name:str = user.user_character_name
        
        user: User = (
            session.query(User)
            .filter(User.user_id == user.user_id)
            .first()
        )
        
        user.user_character_name = nome_sobrenome.title()
        new_name: str = user.user_character_name
        
        session.commit()
        session.close()
        
        await interaction.response.send_message(
            content=(
                f'Nome do usuário {usuário.mention} alterado de `{old_name}` '
                f'para `{new_name}` com sucesso!\n'
                f'Alteração será aplicada nos próximos registros.'
            ),
            ephemeral=True
        )