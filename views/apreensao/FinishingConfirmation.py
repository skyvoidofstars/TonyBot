import discord
import textwrap
from discord import ui
from discord.ext import commands
from dateutil import parser
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from db import Chest, Item, SeizureRefund, _new_session
from utils.UserManager import get_or_create_user
from views.apreensao.functions import new_refund_message_content
from config import brasilia_tz, embed_width, chest_channel_id

def _get_datetime_from_string(string: str) -> datetime:
    _parsed_date: datetime = parser.parse(timestr=string, dayfirst=True)
    if not _parsed_date.tzinfo:
        _datetime: datetime = _parsed_date.replace(tzinfo=brasilia_tz)
    elif _parsed_date.tzinfo != brasilia_tz:
        _datetime: datetime = _parsed_date.astimezone(brasilia_tz)
    _datetime = _datetime.replace(hour=23, minute=59, second=59)

    return _datetime


def _get_upper_limit_date(interaction: discord.Interaction) -> datetime:
    _title: str = interaction.message.embeds[0].title
    _date_string: str = _title.strip()[-6:][:5]  # '````\n01/12\n```' -[-9:]-> '01/12\n```' -[:5]-> '01/12'
    _upper_limit_date: datetime = _get_datetime_from_string(_date_string)

    return _upper_limit_date


def _get_chest_embed(bot: commands.Bot, interaction: discord.Interaction, chest: Chest, item: Item) -> discord.Embed:

    _session: Session = _new_session()

    _stock_qty: int = (
            _session.query(func.sum(Chest.quantity))
            .filter_by(item_id=item.item_id, guild_id=interaction.guild.id)
            .scalar()
            or 0
        )

    _embed: discord.Embed = discord.Embed(
        title='Depósito de reembolsos',
        color=discord.Color.green(),
        timestamp=datetime.now(brasilia_tz),
    )

    _embed.set_author(
        name=interaction.user.name, icon_url=interaction.user.display_avatar.url
    )

    _embed.add_field(
        name='👤 Funcionário',
        value=f'```\n{bot.user.name.ljust(embed_width)}\n```',
        inline=False,
    )
    _embed.add_field(
        name='📦 Item', value=f'```\n{item.item_name}\n```', inline=True
    )
    _embed.add_field(
        name='🔢 Quantidade', value=f'```\n$ {f'{chest.quantity:,}'.replace(',','.')}\n```', inline=True
    )
    _embed.add_field(name='🏷️ Em estoque', value=f'```\n$ {f'{_stock_qty:,}'.replace(',','.')}\n```', inline=True)
    if chest.observations:
        _embed.add_field(
            name='📝 Observações',
            value=f'```\n{'\n'.join(textwrap.wrap(chest.observations, width=embed_width))}\n```',
            inline=False,
        )

    _session.close()

    _embed.set_footer(text=f'ID da movimentação: {chest.chest_id}')

    return _embed

class FinishConfirmationModal(ui.Modal, title='📦 Retenção de valores'):
    confirmation: ui.TextInput = ui.TextInput(
        label='Digite "CONFIRMAR" para reter (irreversível)',
        placeholder='CONFIRMAR',
        required=True,
        style=discord.TextStyle.short,
        max_length=9,
    )

    def __init__(self, bot: commands.Bot, interaction: discord.Interaction, refund_id: int):
        super().__init__(timeout=None)
        self.bot: commands.Bot = bot
        self.original_interaction: discord.Interaction = interaction
        self.refund_id: str = refund_id

    async def on_submit(self, interaction: discord.Interaction):
        confirmation: str = self.confirmation.value
        
        if confirmation.upper() != 'CONFIRMAR':
            await interaction.response.send_message(
                content='Você deve digitar "CONFIRMAR" para finalizar o reembolso.',
                ephemeral=True
            )
            self.stop()
            return
        
        user = get_or_create_user(discord_user=interaction.user)

        session: Session = _new_session()

        refund: SeizureRefund = (
            session.query(SeizureRefund)
            .filter(SeizureRefund.refund_id == self.refund_id)
            .first()
        )

        refund.status = 'FINALIZADO'
        refund.finished_by = user.user_id
        refund.finished_at = datetime.now(brasilia_tz)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            await interaction.response.send_message(
                content='Erro ao finalizar o reembolso.', ephemeral=True
            )
            session.close()
            return

        cash_item: Item = (
            session.query(Item).filter(Item.item_name == 'Dinheiro').scalar()
        )

        chest: Chest = Chest(
            user_id=self.bot.user.id,
            guild_id=interaction.guild.id,
            item_id=cash_item.item_id,
            quantity=refund.total_value - (refund.redeemed_value or 0),
            observations=f'Dinheiro retido do reembolso ID {refund.refund_id}',
            created_at=datetime.now(),
        )

        session.add(chest)
        session.commit()
        session.refresh(chest)

        embed: discord.Embed = _get_chest_embed(
            bot=self.bot,
            interaction=interaction,
            chest=chest,
            item=cash_item
        )

        msg: discord.Message = await interaction.guild.get_channel(
            chest_channel_id
        ).send(embed=embed)

        chest.message_id = msg.id
        chest.channel_id = msg.channel.id
        session.commit()
        session.close()

        upper_limit_date: datetime = _get_upper_limit_date(interaction=interaction)

        finishing_embed: discord.Embed
        finishing_message, finishing_embed = await new_refund_message_content(
            bot=self.bot,
            refund_id=self.refund_id,
            upper_limit_date=upper_limit_date,
            refund_finishing=True,
        )

        finishing_embed.set_field_at(
            index=1,
            name='Não é mais possível confirmar retiradas',
            value=f'Reembolso finalizado por {interaction.user.mention} <t:{int(datetime.now().timestamp())}:R>\n'
            f'O valor restante foi depositado no baú! ({msg.jump_url})',
            inline=False,
        )

        await interaction.message.edit(
            content=finishing_message,
            embed=finishing_embed,
            view=None)
        
        await interaction.response.send_message(
                content='Reembolso finalizado com sucesso e valor depositado no baú.',
                ephemeral=True
            )
        self.stop()