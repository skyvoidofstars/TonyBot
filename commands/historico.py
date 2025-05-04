import discord
from discord.ext import commands
from config import *
from db import NewSession, Chest, Item
from datetime import datetime


def setup_commands(bot:commands.Bot):
    @bot.tree.command(name='histórico', description='Mostra o histórico de movimentações do baú por usuário')
    @discord.app_commands.describe(
        usuário='Usuário a ser consultado'
    )
    async def histórico(interaction:discord.Interaction, usuário:discord.User = None, movimentações:int = 10):
        if usuário is None:
            usuário = interaction.user
        session = NewSession()
        movements = movements = session.query(Item.item, Chest.quantity, Chest.created_at, Chest.guild_id).join(Item, Chest.item_id == Item.id).filter(Chest.user_id == usuário.id, Chest.guild_id == interaction.guild_id).order_by(Chest.created_at.desc()).limit(movimentações).all()

        if not movements:
            await interaction.response.send_message(f'Usuário `{usuário.name}` não possui movimentações registradas!', ephemeral=True)
            session.close()
            return

        summary  = '              Item           |  Qtd.  | Data e hora'.ljust(embed_width) + '\n'
        for item, qty, timestamp, guild in movements:
            if guild == interaction.guild_id:
                prefix = '+' if qty > 0 else '-'
                summary += f'{prefix}{item.ljust(28)[:28]}| {str(abs(qty)).rjust(7) if item != 'Dinheiro' else '$' + str(abs(qty)).rjust(6)}| {timestamp.strftime('%d/%m/%y %H:%M')}\n'

        embed = discord.Embed(
            title=f'📃 Histórico de movimentações do baú de {usuário.name}',
            color=discord.Color.blue(),
            timestamp=datetime.now(brasilia_tz)
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name='', value=f'```diff\n{summary}\n```', inline=False)

        await interaction.response.send_message(embed=embed)
        session.close()