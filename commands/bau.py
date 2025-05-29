import discord, textwrap
from discord.ext import commands
from config import *
from db import NewSession, User, Chest, Item
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime
from utils.user_manager import get_or_create_user

def setup_commands(bot:commands.Bot):
    @bot.tree.command(name='baú', description='Realiza movimentações no baú')
    @discord.app_commands.describe(
        ação='Ação a ser realizada no baú',
        item='Item a ser movimentado',
        quantidade='Quantidade de itens a serem adicionados ou removidos'
    )
    @discord.app_commands.choices(
        ação=[
            discord.app_commands.Choice(name='Adicionar', value='add'),
            discord.app_commands.Choice(name='Remover', value='remove')
        ],
    )
    async def bau(interaction:discord.Interaction, ação: str, item: str, quantidade: int, observação:str = None):
        await interaction.response.defer()
        session: Session = NewSession()
        if interaction.channel_id not in ChestAllowedChannels:
            AllowedChannel = session.query(Chest.channel_id).filter_by(guild_id=interaction.guild.id).scalar()
            if AllowedChannel:
                await interaction.followup.send(f'Esse comando só pode ser usado em {bot.get_channel(AllowedChannel).mention}!')
            else:
                await interaction.followup.send('Nenhum canal permitido configurado para esse servidor!')
            return
        
        ThisItem = session.query(Item).filter_by(item_name=item).first()
        if not ThisItem or quantidade == 0:
            await interaction.followup.send(f'Item `{item}` não está cadastrado ou quantidade não é válida!')
            session.close()
            return
        
        quantidade: int = abs(quantidade)

        user: User = get_or_create_user(session=session, discord_user=interaction.user)
        
        chest: Chest = Chest(
            user_id=user.user_id,
            item_id=ThisItem.item_id,
            quantity=abs(quantidade) if ação == 'add' else -abs(quantidade),
            guild_id=interaction.guild.id,
            created_at=datetime.now(brasilia_tz),
            observations=observação,
        )
        session.add(chest)
        session.commit()
        session.refresh(chest)
        StockQty = session.query(func.sum(Chest.quantity)).filter_by(item_id=ThisItem.item_id).scalar()
        embed = discord.Embed(
            title='Reposição de baú' if ação == 'add' else 'Retirada do baú',
            color=discord.Color.green() if ação == 'add' else discord.Color.dark_red(),
            timestamp=datetime.now(brasilia_tz)
        )
        
        Quantity: str= f'{str(quantidade)}'
        
        if item == 'Dinheiro':
            Quantity: str = f'$ {str(quantidade)}'
            StockQty: str = f'$ {str(StockQty)}'
        
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
        
    @bau.autocomplete('item')
    async def autocomplete_item(interaction: discord.Interaction, current: str):
        session: Session = NewSession()
        items: Item = session.query(Item.item_name).distinct().order_by(Item.item_name).all()
        session.close()

        choices = [
            discord.app_commands.Choice(name=i[0], value=i[0])
            for i in items if i[0] and current.lower() in i[0].lower()
        ][:25]

        await interaction.response.autocomplete(choices)