import discord
from config import *
from db import _new_session, User, Item, Chest
from sqlalchemy import func
from discord.ext import commands
from datetime import datetime


def setup_commands(bot: commands.Bot):
    @bot.tree.command(
        name="ajustar_estoque", description="Ajusta o estoque de um item no baú"
    )
    @discord.app_commands.describe(
        item="Item a ser ajustado",
        quantidade="Quantidade real em estoque",
        tipo_de_ajuste="Tipo de ajuste (padrão: Diferença de estoque)",
    )
    @discord.app_commands.choices(
        tipo_de_ajuste=[
            discord.app_commands.Choice(
                name="Validade ultrapassada", value="Validade ultrapassada"
            ),
            discord.app_commands.Choice(
                name="Diferença de estoque", value="Diferença de estoque"
            ),
        ]
    )
    @discord.app_commands.checks.has_any_role(*allowed_roles)
    async def ajustar_estoque(
        interaction: discord.Interaction,
        item: str,
        quantidade: int,
        tipo_de_ajuste: str = "Diferença de estoque",
    ):
        await interaction.response.defer()
        session = _new_session()
        ThisItem = session.query(Item).filter_by(item_name=item).first()
        user = session.query(User).filter_by(user_id=interaction.user.id).first()
        AdjustmentType = tipo_de_ajuste if tipo_de_ajuste else None
        if not ThisItem or not user:
            await interaction.followup.send(
                f"Item `{ThisItem.item_name}` ou usuário não cadastrado!"
            )
            session.close()
            return

        StockQty = (
            session.query(func.sum(Chest.quantity))
            .filter_by(item_id=ThisItem.item_id, guild_id=interaction.guild_id)
            .scalar()
        )
        if not StockQty:
            StockQty = 0
        StockDiff = quantidade - StockQty

        me = session.query(User).filter_by(user_id=bot.user.id).first()
        if not me:
            me = User(
                user_id=bot.user.id,
                username=bot.user.name,
                user_display_name="Tony, o Mecânico",
                user_character_name="Tony, o Mecânico",
                created_at=datetime.now(brasilia_tz),
            )
            session.add(me)
            session.commit()

        Inventory = Chest(
            user_id=me.user_id,
            guild_id=interaction.guild_id,
            item_id=ThisItem.item_id,
            quantity=StockDiff,
            observations=f"Ajuste de estoque feito por {user.user_character_name};Tipo de ajuste={AdjustmentType}",
            created_at=datetime.now(brasilia_tz),
        )
        session.add(Inventory)
        session.commit()

        embed = discord.Embed(
            title="Ajuste de Estoque",
            color=discord.Color.orange(),
            timestamp=datetime.now(brasilia_tz),
        )

        DiffPrefix = "+" if StockDiff >= 0 else "-"
        StockDiff = f"{abs(StockDiff)}"
        Quantity = f"{str(quantidade)}"

        if item == "Dinheiro":
            StockQty = f"$ {str(StockQty)}"
            Quantity = f"$ {str(quantidade)}"
            StockDiff = f"$ {str(StockDiff)}"

        embed.set_author(
            name=interaction.user.display_name, icon_url=interaction.user.avatar.url
        )

        embed.add_field(
            name="👤 Funcionário",
            value=f"```\n{user.user_character_name.ljust(embed_width)}\n```",
            inline=False,
        )
        embed.add_field(
            name="📦 Item", value=f"```\n{ThisItem.item_name}\n```", inline=True
        )
        embed.add_field(
            name="🔢 Estoque Antigo", value=f"```\n{StockQty}\n```", inline=True
        )
        embed.add_field(
            name="🏷️ Estoque Novo", value=f"```\n{Quantity}\n```", inline=True
        )
        embed.add_field(
            name="📈 Diferença",
            value=f"```diff\n{DiffPrefix} {StockDiff}\n```",
            inline=True,
        )
        embed.add_field(
            name="⚠️ Tipo de Ajuste", value=f"```\n{AdjustmentType}\n```", inline=True
        )
        embed.set_footer(text=f"ID da movimentação: {Inventory.chest_id}")

        msg = await interaction.followup.send(embed=embed)

        Inventory.message_id = msg.id
        Inventory.channel_id = msg.channel.id
        Inventory.guild_id = interaction.guild_id
        session.commit()

        session.close()

    @ajustar_estoque.autocomplete("item")
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
