import discord, textwrap
from discord.ext import commands
from config import *
from db import NewSession, User, Chest, Item
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime
from utils.user_manager import get_or_create_user

async def _is_valid_channel(bot: commands.Bot, interaction: discord.Interaction, session: Session) -> bool:
    if interaction.channel.id not in ChestAllowedChannels:
        AllowedChannel: int | None = session.query(Chest.channel_id).filter_by(guild_id=interaction.guild.id).scalar()
        if AllowedChannel:
            await interaction.followup.send(f'Esse comando só pode ser usado em {bot.get_channel(AllowedChannel).mention}!')
        else:
            await interaction.followup.send('Nenhum canal permitido configurado para esse servidor!')
        return False
    return True

def _format_by_item_name(item: str, value: int) -> str:
    match item:
        case 'Dinheiro':
            return f'$ {str(value)}'
        case _:
            return str(value)
        
def _new_embed(interaction: discord.Interaction, session: Session, chest: Chest, mov_type: int) -> discord.Embed:

    _item_name: str = chest.item.item_name
    _observations: str | None = chest.observations
    _title: str = 'Reposição de baú' if mov_type == 1 else 'Retirada de baú'
    _embed_color: discord.Color = discord.Color.green() if mov_type == 1 else discord.Color.dark_red()
    _employee: str = chest.user.user_character_name.ljust(embed_width)
    _int_stock_qty: int = session.query(func.sum(Chest.quantity)).filter_by(item_id=chest.item.item_id, guild_id=interaction.guild.id).scalar() or 0
    _quantity: str = _format_by_item_name(item=_item_name, value=abs(chest.quantity))
    _stock_qty: str = _format_by_item_name(item=_item_name, value=_int_stock_qty)

    _embed: discord.Embed = discord.Embed(
            title = _title,
            color = _embed_color,
            timestamp = datetime.now(brasilia_tz)
        )

    _embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
    
    _embed.add_field(name='👤 Funcionário', value=f'```\n{_employee}\n```', inline=False)
    _embed.add_field(name='📦 Item', value=f'```\n{_item_name}\n```', inline=True)
    _embed.add_field(name='🔢 Quantidade', value=f'```\n{_quantity}\n```', inline=True)
    _embed.add_field(name='🏷️ Em estoque', value=f'```\n{_stock_qty}\n```', inline=True)
    if _observations:
        _embed.add_field(name='📝 Observações', value=f'```\n{'\n'.join(textwrap.wrap(_observations, width=embed_width))}\n```', inline=False)
    
    _embed.set_footer(text=f'ID da movimentação: {chest.chest_id}')

    return _embed

def setup_commands(bot:commands.Bot):
    bau: discord.app_commands.Group = discord.app_commands.Group(name='baú', description='Realiza movimentações no baú')

    @bau.command(name='adicionar', description='Adicionar um item ao baú')
    @discord.app_commands.describe(
        item='Nome do item a ser adicionado.',
        quantidade='Quantidade do item (deve ser maior que zero).',
        observação='Alguma observação para esta transação?'
    )
    async def adicionar(interaction: discord.Interaction, item: str, quantidade: int, observação: str = None):
        await interaction.response.defer()
        quantidade = abs(quantidade)
        session: Session = NewSession()

        if not await _is_valid_channel(bot=bot, interaction=interaction, session=session):
            session.close()
            return

        ThisItem = session.query(Item).filter_by(item_name=item).first()
        if not ThisItem or quantidade == 0:
            await interaction.followup.send(f'Item `{item}` não está cadastrado ou quantidade não é válida!')
            session.close()
            return
        
        user: User = get_or_create_user(session=session, discord_user=interaction.user)

        chest: Chest = Chest(
            user_id=user.user_id,
            item_id=ThisItem.item_id,
            quantity=quantidade,
            guild_id=interaction.guild.id,
            created_at=datetime.now(brasilia_tz),
            observations=observação,
        )

        session.add(chest)
        session.commit()
        session.refresh(chest)

        embed: discord.Embed = _new_embed(interaction=interaction, session=session, chest=chest, mov_type=1)
        
        msg: discord.Message = await interaction.followup.send(embed=embed)
        chest.message_id = msg.id
        chest.channel_id = msg.channel.id
        session.commit()
        session.close()
    
    @adicionar.autocomplete('item')
    async def autocomplete_adicionar(interaction: discord.Interaction, current: str):
        session: Session = NewSession()
        items: list = (
            session.query(Item.item_name)
            .distinct()
            .order_by(Item.item_name)
            .all()
        )
        session.close()

        choices = [
            discord.app_commands.Choice(name=i[0], value=i[0])
            for i in items if i[0] and current.lower() in i[0].lower()
        ][:25]

        await interaction.response.autocomplete(choices)

    @bau.command(name='retirar', description='Retirar um item do baú')
    @discord.app_commands.describe(
        item='Nome do item a ser retirado.',
        quantidade='Quantidade do item (deve ser maior que zero).',
        observação='Alguma observação para esta transação?'
    )
    async def retirar(interaction: discord.Interaction, item: str, quantidade: int, observação: str = None):
        await interaction.response.defer()
        quantidade = abs(quantidade)
        session: Session = NewSession()

        if not await _is_valid_channel(bot=bot, interaction=interaction, session=session):
            session.close()
            return

        ThisItem = session.query(Item).filter_by(item_name=item).first()
        if not ThisItem or quantidade == 0:
            await interaction.followup.send(f'Item `{item}` não está cadastrado ou quantidade não é válida!')
            session.close()
            return
        
        stock_qty: int = session.query(func.sum(Chest.quantity)).filter_by(item_id=ThisItem.item_id, guild_id=interaction.guild.id).scalar() or 0
        if quantidade > stock_qty:
            await interaction.followup.send(f'Item `{item}` está com o estoque zerado ou a quantidade é maior que a do estoque!\n\nEstoque: {stock_qty}\nQuantidade escolhida: {abs(quantidade)}')
            session.close()
            return
        
        user: User = get_or_create_user(session=session, discord_user=interaction.user)

        chest: Chest = Chest(
            user_id=user.user_id,
            item_id=ThisItem.item_id,
            quantity=-quantidade,
            guild_id=interaction.guild.id,
            created_at=datetime.now(brasilia_tz),
            observations=observação,
        )

        session.add(chest)
        session.commit()
        session.refresh(chest)
        
        embed: discord.Embed = _new_embed(interaction=interaction, session=session, chest=chest, mov_type=-1)

        msg: discord.Message = await interaction.followup.send(embed=embed)
        chest.message_id = msg.id
        chest.channel_id = msg.channel.id
        session.commit()
        session.close()
    
    @retirar.autocomplete('item')
    async def autocomplete_retirar(interaction: discord.Interaction, current: str):
        session: Session = NewSession()
        items: list = (
            session.query(Item.item_name)
            .join(Chest, Chest.item_id == Item.item_id)
            .filter(Chest.guild_id == interaction.guild.id)
            .group_by(Item.item_name)
            .having(func.sum(Chest.quantity) > 0)
            .order_by(Item.item_name)
            .all()
        )
        session.close()

        choices = [
            discord.app_commands.Choice(name=i[0], value=i[0])
            for i in items if i[0] and current.lower() in i[0].lower()
        ][:25]

        await interaction.response.autocomplete(choices)

    bot.tree.add_command(bau)