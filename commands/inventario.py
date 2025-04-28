import discord
from discord.ext import commands
from config import *
from db import NewSession, Chest, Item
from sqlalchemy import func
from datetime import datetime

def setup_commands(bot:commands.Bot):
    @bot.tree.command(name='inventário', description='Mostra o inventário do baú')
    async def inventário(interaction:discord.Interaction):
        try:
            session = NewSession()
            items = session.query(Chest.item, Item.group_name, func.sum(Chest.quantity)).join(Item, Chest.item == Item.item).filter(Chest.guild_id==interaction.guild_id).group_by(Chest.item).having(func.sum(Chest.quantity) != 0).all()

            groups = list(set(item[1] for item in items if item[1]))
            groups.sort()
            
            summary = ''
            for group_name in groups:
                summary += f'#{group_name.ljust(30)}| Quantidade'.ljust(embed_width) + '\n'
                for item, group, qty in items:
                    if group == group_name:
                        summary += f' {item.ljust(30)[:30]}| {'$' + str(qty).rjust(11) if item == 'Dinheiro' else str(qty).rjust(12)}\n'
                summary += '\n'
            
            embed = discord.Embed(
                title='📦 Inventário do baú',
                color=discord.Color.blue(),
                timestamp=datetime.now(brasilia_tz)
            )

            embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
            embed.add_field(name='', value=f'```md\n{summary}\n```', inline=False)

            await interaction.response.send_message(embed=embed)
        except Exception as error:
            await interaction.response.send_message(f'Erro genérico!\n{error}')
        finally:
            session.close()