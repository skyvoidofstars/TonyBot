import discord, re
from discord.ext import commands
from config import *
from db import _new_session, User, Chest, Item
from datetime import datetime


def setup_commands(bot: commands.Bot):
    history = discord.app_commands.Group(
        name="histórico",
        description="Comandos relacionados ao histórico de movimentações do baú",
    )

    @history.command(
        name="usuário",
        description="Mostra o histórico de movimentações do baú por usuário",
    )
    @discord.app_commands.describe(
        usuário="Usuário a ser consultado",
        movimentações="Número de movimentações a serem mostradas (padrão: 10)",
    )
    async def usuário(
        interaction: discord.Interaction,
        usuário: discord.User = None,
        movimentações: int = 10,
    ):
        if usuário is None:
            usuário = interaction.user

        session = _new_session()

        movements = (
            session.query(
                Chest.chest_id,
                Item.item_name,
                Chest.quantity,
                Chest.created_at,
                Chest.guild_id,
            )
            .join(Item, Chest.item_id == Item.item_id)
            .filter(Chest.user_id == usuário.id, Chest.guild_id == interaction.guild_id)
            .order_by(Chest.created_at.desc())
            .limit(movimentações)
            .all()
        )

        if not movements:
            await interaction.response.send_message(
                f"Usuário `{usuário.name}` não possui movimentações registradas!",
                ephemeral=True,
            )
            session.close()
            return

        summary = (
            "  ID  |         Item        |  Qtd.  | Data e hora".ljust(embed_width)
            + "\n"
        )
        for id, item, qty, timestamp, guild in movements:
            if guild == interaction.guild_id:
                prefix = "+" if qty > 0 else "-"
                summary += f"{prefix}{str(id).rjust(5)}| {item.ljust(20)[:20]}| {str(abs(qty)).rjust(7) if item != 'Dinheiro' else '$' + str(abs(qty)).rjust(6)}| {timestamp.strftime('%d/%m/%y %H:%M')}\n"

        embed = discord.Embed(
            title=f"📃 Histórico de movimentações do baú de {usuário.name}",
            color=discord.Color.blue(),
            timestamp=datetime.now(brasilia_tz),
        )
        embed.set_author(
            name=interaction.user.name, icon_url=interaction.user.display_avatar.url
        )
        embed.add_field(name="", value=f"```diff\n{summary}\n```", inline=False)

        await interaction.response.send_message(embed=embed)
        session.close()

    @history.command(
        name="item", description="Mostra o histórico de movimentações do baú por item"
    )
    @discord.app_commands.describe(
        item="Item a ser consultado",
        movimentações="Número de movimentações a serem mostradas (padrão: 10)",
    )
    async def item(
        interaction: discord.Interaction, item: str, movimentações: int = 10
    ):

        session = _new_session()
        item = session.query(Item).filter(Item.item_name == item).first()

        if not item:
            await interaction.response.send_message(
                f"Item `{item}` não encontrado!", ephemeral=True
            )
            session.close()
            return

        movements = (
            session.query(
                Chest.chest_id,
                User.user_character_name,
                Chest.quantity,
                Chest.created_at,
                Chest.guild_id,
            )
            .join(User, Chest.user_id == User.user_id)
            .filter(
                Chest.item_id == item.item_id, Chest.guild_id == interaction.guild_id
            )
            .order_by(Chest.created_at.desc())
            .limit(movimentações)
            .all()
        )

        if not movements:
            await interaction.response.send_message(
                f"Item `{item.item_name}` não possui movimentações registradas!",
                ephemeral=True,
            )
            session.close()
            return

        summary = (
            "  ID  |        Usuário       |  Qtd.  | Data e hora".ljust(embed_width)
            + "\n"
        )
        for id, user, qty, timestamp, guild in movements:
            if guild == interaction.guild_id:
                prefix = "+" if qty > 0 else "-"
                summary += f"{prefix}{str(id).rjust(5)}| {user.ljust(21)[:21]}| {str(abs(qty)).rjust(7) if item != 'Dinheiro' else '$' + str(abs(qty)).rjust(6)}| {timestamp.strftime('%d/%m/%y %H:%M')}\n"

        embed = discord.Embed(
            title=f"📃 Histórico de movimentações do baú do item {item.item_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now(brasilia_tz),
        )
        embed.set_author(
            name=interaction.user.name, icon_url=interaction.user.display_avatar.url
        )
        embed.add_field(name="", value=f"```diff\n{summary}\n```", inline=False)

        await interaction.response.send_message(embed=embed)
        session.close()

    @item.autocomplete("item")
    async def autocomplete_item(interaction: discord.Interaction, current: str):
        session = _new_session()
        items = session.query(Item.item_name).distinct().order_by(Item.item_name).all()
        session.close()

        choices = [
            discord.app_commands.Choice(name=i[0], value=i[0])
            for i in items
            if i[0] and current.lower() in i[0].lower()
        ][:25]

        await interaction.response.autocomplete(choices)

    @history.command(
        name="ajustes",
        description="Mostra o histórico de movimentações do baú por item",
    )
    async def ajustes(interaction: discord.Interaction):
        session = _new_session()
        movements = (
            session.query(
                Chest.chest_id, Item.item_name, Chest.quantity, Chest.observations
            )
            .join(Item, Chest.item_id == Item.item_id)
            .filter(
                Chest.user_id == bot.user.id, Chest.guild_id == interaction.guild_id
            )
            .order_by(Chest.created_at.desc())
            .limit(25)
            .all()
        )

        if not movements:
            await interaction.response.send_message(
                f"Não há ajustes de estoque registrados!", ephemeral=True
            )
            session.close()
            return

        summary = (
            "  ID  |       Item      |  Qtd.  |        Tipo       ".ljust(embed_width)[
                :embed_width
            ]
            + "\n"
        )
        for id, item, qty, observations in movements:

            regex_type: str = "(?<=Tipo de ajuste=).*$"
            adjustment_type = re.search(regex_type, observations)

            prefix = "+" if qty > 0 else "-"
            summary += (
                f"{prefix}{str(id).rjust(5)}| {item.ljust(16)[:16]}| {str(abs(qty)).rjust(7) if item != 'Dinheiro' else '$' + str(abs(qty)).rjust(6)}| {adjustment_type.group() if adjustment_type else 'Sem descrição'}".ljust(
                    embed_width
                )[
                    :embed_width
                ]
                + "\n"
            )

        embed = discord.Embed(
            title=f"📝 Histórico de ajustes de estoque",
            color=discord.Color.blue(),
            timestamp=datetime.now(brasilia_tz),
        )
        embed.set_author(
            name=interaction.user.name, icon_url=interaction.user.display_avatar.url
        )
        embed.add_field(name="", value=f"```diff\n{summary}\n```", inline=False)

        await interaction.response.send_message(embed=embed)
        session.close()

    bot.tree.add_command(history)
