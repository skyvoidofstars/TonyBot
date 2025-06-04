import discord, regex
from discord import ui
from discord.ext import commands
from datetime import datetime
from dateutil import parser
from sqlalchemy import func
from sqlalchemy.orm import Session
from db import User, Seizure, SeizureRefund, _new_session
from utils.UserManager import get_or_create_user
from utils.ErrorReporting import log_and_notify
from views.apreensao.functions import new_refund_message_content
from config import brasilia_tz, seizure_value, refund_channel_id


def _get_refund_id(interaction: discord.Interaction) -> int:
    _pattern: str = r"[0-9]+"
    _string: str = interaction.message.embeds[0].footer.text
    _match_str: str = regex.search(pattern=_pattern, string=_string).group(0)
    _refund_id: int = int(_match_str.strip())

    return _refund_id


def _add_refund_confirmation(user: discord.User, refund_id: int) -> bool:
    _session: Session = _new_session()
    _user_seizure_list: list[Seizure] = (
        _session.query(Seizure)
        .filter(
            Seizure.user_id == user.id,
            Seizure.refund_id == refund_id,
            Seizure.status == "REEMBOLSADO",
        )
        .all()
    )
    if not _user_seizure_list:
        _session.close()
        return False

    for _seizure in _user_seizure_list:
        _seizure.status = "RESGATADO"
        _seizure.redeemed_at = datetime.now(brasilia_tz)
    _session.commit()
    _session.close()
    return True


def _get_datetime_from_string(string: str) -> datetime:
    _parsed_date: datetime = parser.parse(timestr=string, dayfirst=True)
    if not _parsed_date.tzinfo:
        _datetime: datetime = _parsed_date.replace(tzinfo=brasilia_tz)
    elif _parsed_date.tzinfo != brasilia_tz:
        _datetime: datetime = _parsed_date.astimezone(brasilia_tz)
    _datetime = _datetime.replace(hour=23, minute=59, second=59)

    return _datetime


def _update_refund_redeemed_value(refund_id: int):
    _session: Session = _new_session()
    _redeemed_value: int = (
        _session.query(
            (func.count(Seizure.redeemed_at) * seizure_value).label(
                "redeemed_total_value"
            )
        )
        .filter(Seizure.refund_id == refund_id)
        .scalar()
    )
    _refund: SeizureRefund = (
        _session.query(SeizureRefund)
        .filter(SeizureRefund.refund_id == refund_id)
        .first()
    )
    _refund.redeemed_value = _redeemed_value

    try:
        _session.commit()
    except Exception as e:
        _session.rollback()
        print(f"Erro ao atualizar valor resgatado do reembolso de ID: {refund_id}")
    finally:
        _session.close()


def _get_upper_limit_date(interaction: discord.Interaction) -> datetime:
    _field_value: str = interaction.message.embeds[0].fields[0].value
    _date_string: str = _field_value.strip()[-9:][
        :5
    ]  # '````\n01/12\n```' -[-9:]-> '01/12\n```' -[:5]-> '01/12'
    _upper_limit_date: datetime = _get_datetime_from_string(_date_string)

    return _upper_limit_date


class RefundButtonsView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.custom_id = f"confirm_refund_persistant_view"

    @ui.button(
        label="Confirmar recebimento",
        style=discord.ButtonStyle.success,
        custom_id="confirm_refund_button",
    )
    async def confirmar_recebimento(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        try:
            refund_id: int = _get_refund_id(interaction=interaction)
        except Exception as e:
            await interaction.response.send_message(
                content="Erro ao obter o ID do reembolso.", ephemeral=True
            )
            return

        is_refund_confirmed: bool = _add_refund_confirmation(
            user=interaction.user, refund_id=refund_id
        )
        if not is_refund_confirmed:
            await interaction.response.send_message(
                content="Você não está na lista ou já resgatou os valores",
                ephemeral=True,
            )
            return

        _update_refund_redeemed_value(refund_id=refund_id)

        session: Session = _new_session()
        pendents_count: int = (
            session.query(func.count(Seizure.user_id))
            .filter(Seizure.status == "REEMBOLSADO", Seizure.refund_id == refund_id)
            .scalar()
        )

        upper_limit_date: datetime = _get_upper_limit_date(interaction=interaction)

        message_content: str | None
        message_embed: discord.Embed

        message_content, message_embed = await new_refund_message_content(
            bot=self.bot, refund_id=refund_id, upper_limit_date=upper_limit_date
        )
        if pendents_count > 0:
            await interaction.message.edit(content=message_content, embed=message_embed)
            await interaction.response.send_message(
                content="Recebimento confirmado!", ephemeral=True, delete_after=3
            )
        else:
            message_embed.color = discord.Color.red()
            message_embed.set_field_at(
                index=2,
                name="Reembolso finalizado",
                value=f"Todos os funcionários resgataram seus valores <t:{int(datetime.now().timestamp())}:R>",
                inline=False,
            )
            await interaction.message.edit(
                content=message_content, embed=message_embed, view=None
            )
            await interaction.response.send_message(
                content="Recebimento confirmado!", ephemeral=True, delete_after=3
            )

            refund: SeizureRefund = (
                session.query(SeizureRefund)
                .filter(SeizureRefund.refund_id == refund_id)
                .first()
            )

            refund.status = "FINALIZADO"
            refund.finished_at = datetime.now(brasilia_tz)
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                await interaction.response.send_message(
                    content="Erro ao finalizar o reembolso.", ephemeral=True
                )
            self.stop()

        session.close()

    @ui.button(
        label="Finalizar pagamentos",
        style=discord.ButtonStyle.danger,
        custom_id="finish_payments_button",
    )
    async def sup_finalizar_pagamento(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        try:
            refund_id: int = _get_refund_id(interaction=interaction)
        except Exception as e:
            await interaction.response.send_message(
                content="Erro ao obter o ID do reembolso.", ephemeral=True
            )
            return

        user = get_or_create_user(discord_user=interaction.user)

        session: Session = _new_session()

        refund: SeizureRefund = (
            session.query(SeizureRefund)
            .filter(SeizureRefund.refund_id == refund_id)
            .first()
        )

        refund.status = "FINALIZADO"
        refund.finished_by = user.user_id
        refund.finished_at = datetime.now(brasilia_tz)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            await interaction.response.send_message(
                content="Erro ao finalizar o reembolso.", ephemeral=True
            )
            return
        finally:
            session.close()

        upper_limit_date: datetime = _get_upper_limit_date(interaction=interaction)

        finishing_message: str
        finishing_embed: discord.Embed
        finishing_message, finishing_embed = await new_refund_message_content(
            bot=self.bot,
            refund_id=refund_id,
            upper_limit_date=upper_limit_date,
            refund_finishing=True,
        )

        finishing_embed.set_field_at(
            index=2,
            name="Não é mais possível confirmar retiradas",
            value=f"Reembolso finalizado por {interaction.user.mention} <t:{int(datetime.now().timestamp())}:R>\n"
            "O valor restante foi depositado no baú!",
            inline=False,
        )

        await interaction.message.edit(
            content=finishing_message, embed=finishing_embed, view=None
        )
        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: str, item):
        await log_and_notify(bot=self.bot, interaction=interaction, text=error)
        return super().on_error(interaction, error, item)
