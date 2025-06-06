import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from datetime import datetime, date
from dateutil import parser
from db import User, Seizure, _new_session
from config import allowed_roles, brasilia_tz, seizure_value
from utils.ImageManager import get_seizure_report_image
from views.apreensao.ApproveRefunds import ApproveRefundView


def _get_datetime_from_string(string: str) -> datetime:
    _parsed_date: datetime = parser.parse(timestr=string, dayfirst=True)
    if not _parsed_date.tzinfo:
        _datetime: datetime = _parsed_date.replace(tzinfo=brasilia_tz)
    elif _parsed_date.tzinfo != brasilia_tz:
        _datetime: datetime = _parsed_date.astimezone(brasilia_tz)
    _datetime = _datetime.replace(hour=23, minute=59, second=59)

    return _datetime


def _get_valid_seizure_count(
    lower_limit_date: datetime, upper_limit_date: datetime
) -> int:
    session: Session = _new_session()
    _valid_seizure_count: int = (
        session.query(func.count(Seizure.seizure_id))
        .filter(
            or_(Seizure.status == 'CRIADO', Seizure.status == 'REEMBOLSADO'),
            Seizure.created_at >= lower_limit_date,
            Seizure.created_at <= upper_limit_date,
        )
        .scalar()
    )
    session.close()

    return _valid_seizure_count


def setup_commands(bot: commands.Bot):
    apreensoes: app_commands.Group = app_commands.Group(
        name='apreensão', description='Controle de apreensões'
    )

    @apreensoes.command(
        name='publicar-reembolsos', description='Gerar informações sobre fechamento'
    )
    @app_commands.checks.has_any_role(*allowed_roles)
    @app_commands.describe(data_fim=f'Ex: {date.today().strftime('%d/%m/%y')}')
    async def publicar_reembolsos(interaction: discord.Interaction, data_fim: str):
        try:
            upper_limit_date: datetime = _get_datetime_from_string(data_fim)
        except (ValueError, TypeError, parser.ParserError) as e:
            await interaction.response.send_message(
                content=f'Falha ao extrair data de `{data_fim}`, verifique e tente novamente'
            )
            return

        session: Session = _new_session()
        seizure_list: list[tuple[str, int]] = (
            session.query(
                User.user_character_name,
                (func.count(Seizure.seizure_id) * seizure_value).label('total_value'),
            )
            .join(User, User.user_id == Seizure.user_id)
            .filter(Seizure.status == 'CRIADO', Seizure.created_at <= upper_limit_date)
            .group_by(User.user_character_name)
            .order_by(User.user_character_name)
        )

        lower_limit_date: datetime = (
            session.query(func.min(Seizure.created_at).label(''))
            .filter(Seizure.status == 'CRIADO')
            .scalar()
        ) or datetime.now(brasilia_tz)

        session.close()

        dates_interval: str = f'{lower_limit_date.strftime(format='%d/%m')} - {upper_limit_date.strftime(format='%d/%m')}'

        if seizure_list.count() == 0:
            await interaction.response.send_message(
                content=f'Nenhuma apreensão encontrada até {upper_limit_date.strftime(format='%d/%m/%y')}'
            )
            return

        output: str = (
            f'Período ({dates_interval})\n' f'{'Nome'.ljust(50)} | Valor total\n\n'
        )
        _total_value: int = 0
        for _character, _value in seizure_list:
            _total_value += _value
            value = f'{_value:,}'.replace(',', '.')

            output += f'{_character.ljust(50)} | $ {value.rjust(6)}\n'

        total_value: str = f'{_total_value:,}'.replace(',', '.')

        output += f'\nValor total: $ {total_value}'
        output = (
            f'```\n{output}```\n'
            f'### Clique no botão abaixo para confirmar e publicar os reembolsos'
        )

        await interaction.response.send_message(content=output)
        message: discord.Message = await interaction.original_response()
        await message.edit(
            content=message.content,
            view=ApproveRefundView(
                bot=bot, original_message=message, limit_date=upper_limit_date
            ),
        )

    @apreensoes.command(
        name='relatório', description='Cria uma imagem de relatório de apreensões'
    )
    @app_commands.checks.has_any_role(*allowed_roles)
    @app_commands.describe(data_fim=f'Ex: {date.today().strftime('%d/%m/%y')}')
    async def relatório(
        interaction: discord.Interaction, data_início: str, data_fim: str
    ):
        try:
            upper_limit_date: datetime = _get_datetime_from_string(data_fim)
            lower_limit_date: datetime = _get_datetime_from_string(data_início)
        except (ValueError, TypeError, parser.ParserError) as e:
            await interaction.response.send_message(
                content=f'Falha ao extrair data de `{data_início}` ou de `{data_fim}`, verifique e tente novamente'
            )
            print(e)
            return

        await interaction.response.send_message(
            content='Aguarde enquando o relatório é gerado...'
        )

        awating_message: discord.Message = await interaction.original_response()

        _valid_seizure_count: int = _get_valid_seizure_count(
            lower_limit_date=lower_limit_date, upper_limit_date=upper_limit_date
        )

        dates_interval: str = f'{lower_limit_date.strftime(format='%d/%m/%Y')} à {upper_limit_date.strftime(format='%d/%m/%Y')}'

        image_file: discord.File = get_seizure_report_image(
            dates_interval=dates_interval, tow_count=_valid_seizure_count
        )

        await interaction.channel.send(
            content=f'Relatório gerado por {interaction.user.mention}', file=image_file
        )

        await awating_message.edit(
            content='Relatório gerado! Apagando a mensagem...', delete_after=5
        )

    bot.tree.add_command(apreensoes)
