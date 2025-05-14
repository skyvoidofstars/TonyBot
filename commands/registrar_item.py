import discord
from discord.ext import commands
from config import *
from sqlalchemy import func
from db import NewSession, User, Item
from datetime import datetime

def setup_commands(bot:commands.Bot):
    @bot.tree.command(name='registrar_item', description='Registra um item no sistema')
    @discord.app_commands.checks.has_any_role(*AllowedRoles)
    @discord.app_commands.describe(
        item='Nome do item a ser registrado',
        categoria='Categoria do item a ser registrado',
        descrição='Descrição do item a ser registrado'
    )
    async def registrar_item(interaction:discord.Interaction, item:str, categoria:str, descrição:str = None):
        await interaction.response.defer()
        session = NewSession()
        
        user = session.query(User).filter_by(user_id=interaction.user.id).first()
        if not user:
            user = User(
                user_id=interaction.user.id,
                username=interaction.user.name,
                user_display_name=interaction.user.display_name,
                user_character_name=interaction.user.display_name.split('|')[0].strip(),
                created_at=datetime.now(brasilia_tz)
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        
        if session.query(Item).filter(func.lower(Item.item_name) == item.lower()).first():
            await interaction.followup.send(f'Item `{item}` já está cadastrado!', ephemeral=True)
            session.close()
            return
        
        NewItem = Item(
            item_name=item,
            group_name=categoria,
            description=descrição,
            created_by=user.user_id,
            created_at=datetime.now(brasilia_tz)
        )
        session.add(NewItem)
        session.commit()
        session.refresh(NewItem)
        session.close()
        
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Item `{item}` registrado por {user.user_character_name} ({user.user_id})')

        embed = discord.Embed(
            title='Item registrado com sucesso!',
            color=discord.Color.green(),
            timestamp=datetime.now(brasilia_tz)
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        
        embed.add_field(name='👤 Funcionário', value=f'```\n{user.user_character_name.ljust(embed_width)}\n```', inline=False)
        embed.add_field(name='📦 Item', value=f'```\n{item}\n```', inline=True)
        embed.add_field(name='🏷️ Categoria', value=f'```\n{categoria}\n```', inline=True)
        embed.add_field(name='📝 Descrição', value=f'```\n{descrição if descrição else 'Sem descrição'}\n```', inline=False)
        
        embed.set_footer(text=f'ID do item: {NewItem.item_id}')
        
        await interaction.followup.send(embed=embed)
        
    @registrar_item.autocomplete('categoria')
    async def autocomplete_categoria(interaction: discord.Interaction, current: str):
        session = NewSession()
        categorias = session.query(Item.group_name).distinct().order_by(Item.group_name).all()
        session.close()

        choices = [
            discord.app_commands.Choice(name=c[0], value=c[0])
            for c in categorias if c[0] and current.lower() in c[0].lower()
        ]

        await interaction.response.autocomplete(choices)