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
        AllowedChannel: Chest | None = session.query(Chest.channel_id).filter_by(guild_id=interaction.guild.id).scalar()
        if AllowedChannel:
            await interaction.followup.send(f'Esse comando só pode ser usado em {bot.get_channel(AllowedChannel).mention}!')
        else:
            await interaction.followup.send('Nenhum canal permitido configurado para esse servidor!')
        return False
    return True

def setup_commands(bot:commands.Bot):
    bau: discord.app_commands.Group = discord.app_commands.Group(name='baú', description='Realiza movimentações no baú')

    @bau.command(name='adicionar', description='Adiciona um item ao baú')
    @discord.app_commands.describe(
        item='Nome do item a ser adicionado.',
        quantidade='Quantidade do item (deve ser maior que zero).',
        observação='Alguma observação para esta transação?'
    )
    async def adicionar(interaction: discord.Interaction, item: str, quantidade: int, observação: str = None):
        await interaction.response.defer()
        session: Session = NewSession()
        ThisItem = session.query(Item).filter_by(item_name=item).first()

        if not await _is_valid_channel(bot=bot, interaction=interaction, session=session):
            session.close()
            return

        if not ThisItem or quantidade == 0:
            await interaction.followup.send(f'Item `{item}` não está cadastrado ou quantidade não é válida!')
            session.close()
            return
        
        quantidade = abs(quantidade)
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

        Quantity: str = str(quantidade)
        StockQty: int = session.query(func.sum(Chest.quantity)).filter_by(item_id=ThisItem.item_id, guild_id=interaction.guild.id).scalar()
        if item == 'Dinheiro':
            Quantity: str = f'$ {str(quantidade)}'
            StockQty: str = f'$ {str(StockQty)}'
        
        embed: discord.Embed = discord.Embed(
            title='Reposição de baú',
            color=discord.Color.green(),
            timestamp=datetime.now(brasilia_tz)
        )

        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        
        embed.add_field(name='👤 Funcionário', value=f'```\n{user.user_character_name.ljust(embed_width)}\n```', inline=False)
        embed.add_field(name='📦 Item', value=f'```\n{ThisItem.item_name}\n```', inline=True)
        embed.add_field(name='🔢 Quantidade', value=f'```\n{Quantity}\n```', inline=True)
        embed.add_field(name='🏷️ Em estoque', value=f'```\n{StockQty}\n```', inline=True)
        if observação:
            embed.add_field(name='📝 Observações', value=f'```\n{'\n'.join(textwrap.wrap(observação, width=embed_width))}\n```', inline=False)
        
        embed.set_footer(text=f'ID da movimentação: {chest.chest_id}')
        
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
        session: Session = NewSession()
        ThisItem = session.query(Item).filter_by(item_name=item).first()

        if not await _is_valid_channel(bot=bot, interaction=interaction, session=session):
            session.close()
            return

        if not ThisItem or quantidade == 0:
            await interaction.followup.send(f'Item `{item}` não está cadastrado ou quantidade não é válida!')
            session.close()
            return
        
        StockQty: int = session.query(func.sum(Chest.quantity)).filter_by(item_id=ThisItem.item_id, guild_id=interaction.guild.id).scalar() or 0
        quantidade = abs(quantidade)
        if quantidade > StockQty:
            await interaction.followup.send(f'Item `{item}` está com o estoque zerado ou a quantidade é maior que a do estoque!\n\nEstoque: {StockQty}\nQuantidade escolhida: {abs(quantidade)}')
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

        Quantity: str = str(quantidade)
        StockQty: int = session.query(func.sum(Chest.quantity)).filter_by(item_id=ThisItem.item_id, guild_id=interaction.guild.id).scalar()
        if item == 'Dinheiro':
            Quantity: str = f'$ {str(quantidade)}'
            StockQty: str = f'$ {str(StockQty)}'
        
        embed: discord.Embed = discord.Embed(
            title='Retirada do baú',
            color=discord.Color.dark_red(),
            timestamp=datetime.now(brasilia_tz)
        )

        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        
        embed.add_field(name='👤 Funcionário', value=f'```\n{user.user_character_name.ljust(embed_width)}\n```', inline=False)
        embed.add_field(name='📦 Item', value=f'```\n{ThisItem.item_name}\n```', inline=True)
        embed.add_field(name='🔢 Quantidade', value=f'```\n{Quantity}\n```', inline=True)
        embed.add_field(name='🏷️ Em estoque', value=f'```\n{StockQty}\n```', inline=True)
        if observação:
            embed.add_field(name='📝 Observações', value=f'```\n{'\n'.join(textwrap.wrap(observação, width=embed_width))}\n```', inline=False)
        
        embed.set_footer(text=f'ID da movimentação: {chest.chest_id}')
        
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