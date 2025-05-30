import discord, textwrap
from discord.ext import commands
from config import *
from sqlalchemy import func
from db import _new_session, Chest
from datetime import datetime

def setup_commands(bot:commands.Bot):
    @bot.tree.command(name='ver_registro', description='Recupera um registro de movimentação')
    @discord.app_commands.checks.has_any_role(*AllowedRoles)
    @discord.app_commands.describe(
        id='ID do registro a ser recuperado',
    )
    async def ver_registro(interaction:discord.Interaction, id:int):
        session = _new_session()
        
        chest = session.query(Chest).filter_by(chest_id=id).first()
        
        if not chest:
            await interaction.response.send_message(f'Nenhum registro encontrado com o ID `{id}`.', ephemeral=True)
            session.close()
            return
    
        embed = discord.Embed(
            title='Reposição de baú' if chest.quantity >= 0 else 'Retirada do baú',
            color=discord.Color.green() if chest.quantity >= 0 else discord.Color.dark_red(),
            timestamp=datetime.now(brasilia_tz)
        )
        
        Quantity = f'{str(chest.quantity)}'
        StockQty = session.query(func.sum(Chest.quantity)).filter(Chest.item_id == chest.item_id, Chest.created_at <= chest.created_at).scalar()
        
        if chest.item.item_name == 'Dinheiro':
            Quantity = f'$ {str(chest.quantity)}'
            StockQty = f'$ {str(StockQty)}'
        
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        
        embed.add_field(name='👤 Funcionário', value=f'```\n{chest.user.user_character_name.ljust(embed_width)}\n```', inline=False)
        embed.add_field(name='📦 Item', value=f'```\n{chest.item.item_name}\n```', inline=True)
        embed.add_field(name='🔢 Quantidade', value=f'```\n{Quantity}\n```', inline=True)
        embed.add_field(name='🏷️ Em estoque', value=f'```\n{StockQty}\n```', inline=True)
        if chest.observations:
            embed.add_field(name='📝 Observações', value=f'```\n{'\n'.join(textwrap.wrap(chest.observations, width=embed_width))}\n```', inline=False)
        
        embed.set_footer(text=f'ID da movimentação: {chest.chest_id}')
        
        await interaction.response.send_message(embed=embed)
    
        session.close()
        