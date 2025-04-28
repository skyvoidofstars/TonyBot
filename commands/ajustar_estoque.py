import discord
from config import *
from db import NewSession, User, Item, Chest
from sqlalchemy import func
from discord.ext import commands
from datetime import datetime


def setup_commands(bot:commands.Bot):
    @bot.tree.command(name='ajustar_estoque', description='Ajusta o estoque de um item no baú')
    @discord.app_commands.describe(
        item='Item a ser ajustado',
        quantidade='Quantidade real em estoque'
    )
    async def ajustar_estoque(interaction: discord.Interaction, item:str, quantidade:int):
        if not any(role.id in AllowedRoles for role in interaction.user.roles):
            await interaction.response.send_message('Você não tem permissão para usar esse comando!', ephemeral=True, delete_after=5)
            return
        await interaction.response.defer()
        try:
            session = NewSession()
            if not session.query(Item).filter_by(item=item).first():
                await interaction.followup.send(f'Item `{item}` não está cadastrado!')
                session.close()
                return

            StockQty = session.query(func.sum(Chest.quantity)).filter_by(item=item, guild_id=interaction.guild_id).scalar()
            StockDiff = quantidade - StockQty
            
            me = session.query(User).filter_by(user_id=bot.user.id).first()
            if not me:
                me = User(
                    user_id=bot.user.id,
                    username=bot.user.name,
                    user_global_name='Tony, o Mecânico',
                    user_display_name='Tony, o Mecânico',
                    user_character_name='Tony, o Mecânico',
                    created_at=datetime.now(brasilia_tz)
                )
                session.add(me)
                session.commit()
                        
            Inventory = Chest(
                user_id=me.user_id,
                guild_id=interaction.guild_id,
                item=item,
                quantity=StockDiff,
                observations=f'Ajuste de estoque feito por {interaction.user.display_name}',
                created_at=datetime.now(brasilia_tz)
            )
            session.add(Inventory)
            session.commit()
            
            embed = discord.Embed(
                title='Ajuste de Estoque',
                color=discord.Color.orange(),
                timestamp=datetime.now(brasilia_tz)
            )
            
            if item == 'Dinheiro':
                StockQty = f'$ {str(StockQty)}'
                Quantity = f'$ {str(quantidade)}'
                StockDiff = f'$ {str(StockDiff)}'
            
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)
            
            embed.add_field(name='👤 Funcionário', value=f'```\n{interaction.user.display_name.ljust(embed_width)}\n```', inline=False)
            embed.add_field(name='📦 Item', value=f'```\n{item}\n```', inline=True)
            embed.add_field(name='🔢 Estoque Antigo', value=f'```\n{StockQty}\n```', inline=True)
            embed.add_field(name='🏷️ Estoque Novo', value=f'```\n{Quantity}\n```', inline=True)
            embed.add_field(name='📈 Diferença', value=f'```diff\n{'+' if StockDiff >= 0 else '-'} {abs(StockDiff)}\n```', inline=True)
            
            embed.set_footer(text=f'ID da movimentação: {Inventory.id}')
            
            msg = await interaction.followup.send(embed=embed)
            
            Inventory.message_id = msg.id
            Inventory.channel_id = msg.channel.id
            Inventory.guild_id = interaction.guild_id
            session.commit()
            
        except Exception as e:
            await interaction.followup.send(f'Erro genérico!\n{e}')
        finally:
            session.close()
            
    @ajustar_estoque.autocomplete('item')
    async def autocomplete_item(interaction: discord.Interaction, current: str):
        session = NewSession()
        items = session.query(Item.item).distinct().order_by(Item.item).all()
        session.close()

        choices = [
            discord.app_commands.Choice(name=i[0], value=i[0])
            for i in items if i[0] and current.lower() in i[0].lower()
        ][:25]

        await interaction.response.autocomplete(choices)