import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime
from dateutil import parser
from db import User, Seizure, _new_session
from config import AllowedRoles, brasilia_tz, seizure_value
from utils.ErrorReporting import log_and_notify
from views.apreensao.ApproveRefunds import ApproveRefundView

def _get_datetime_from_string(string: str) -> datetime:
    _parsed_date: datetime = parser.parse(timestr=string, dayfirst=True)
    if not _parsed_date.tzinfo:
        _datetime: datetime = _parsed_date.replace(tzinfo=brasilia_tz)
    elif _parsed_date.tzinfo != brasilia_tz:
        _datetime: datetime = _parsed_date.astimezone(brasilia_tz)
    _datetime = _datetime.replace(hour=23, minute=59, second=59)
    
    return _datetime
def setup_commands(bot: commands.Bot):
    apreensoes: app_commands.Group = app_commands.Group(name='apreensao', description='Controle de apreensões')
        
    @apreensoes.command(name='resumo', description='Gerar informações sobre fechamento')
    @app_commands.checks.has_any_role(*AllowedRoles)
    @app_commands.describe(
        data_limite = 'Ex: 31/05/2025'
    )
    async def resumo(interaction: discord.Interaction, data_limite:str):
        try:
            upper_limit_date: datetime = _get_datetime_from_string(data_limite)
        except (ValueError, TypeError, parser.ParserError) as e:
            await interaction.response.send_message(content=f'Falha ao extrair data de `{data_limite}`, verifique e tente novamente')
            return
        
        session: Session = _new_session()
        seizure_list: list[tuple[str, int]] = (
            session.query(User.user_character_name, (func.count(Seizure.seizure_id) * seizure_value).label('total_value'))
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
            await interaction.response.send_message(content=f'Nenhuma apreensão encontrada até {upper_limit_date.strftime(format='%d/%m/%y')}')
            return
        
        output: str = (
            f'Período ({dates_interval})\n'
            f'{'Nome'.ljust(50)} | Valor total\n\n'
        )
        _total_value: int = 0
        for _character, _value in seizure_list:
            _total_value += _value
            value = f'{_value:,}'.replace(',','.')
            
            output += f'{_character.ljust(50)} | $ {value.rjust(6)}\n'
        
        total_value: str = f'{_total_value:,}'.replace(',','.')
        
        output += f'\nValor total: $ {total_value}'
        output = (
            f'```\n{output}```\n'
            f'### Clique no botão abaixo para confirmar e publicar os reembolsos'
            )
        
        await interaction.response.send_message(content=output)
        message: discord.Message = await interaction.original_response()
        await message.edit(content=message.content, view=ApproveRefundView(bot=bot, original_message=message, limit_date=upper_limit_date))
    
    bot.tree.add_command(apreensoes)