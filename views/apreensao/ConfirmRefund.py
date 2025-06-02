import discord, regex
from discord import ui
from discord.ext import commands
from datetime import datetime
from dateutil import parser
from sqlalchemy.orm import Session
from db import Seizure, _new_session 
from views.apreensao.functions import new_refund_message_content
from config import brasilia_tz

def _original_refund_information(string: str):
    _pattern = r'(?<=\`\`\`diff)[\s\S]*?(?=\n\`\`\`)'
    _match_str: str = regex.search(pattern=_pattern, string=string).group(0)
    
    return _match_str.strip()

def _get_refund_id(interaction: discord.Interaction) -> int:
    _pattern: str = r'(?<=sob o ID )[0-9]+'
    _string: str = interaction.message.content
    _match_str: str = regex.search(pattern=_pattern, string=_string).group(0)
    _refund_id: int = int(_match_str.strip())
    
    return _refund_id

def _add_refund_confirmation(user: discord.User, refund_id: int) -> bool:
    _session: Session = _new_session()
    _user_seizure_list: list[Seizure] = (
        _session.query(Seizure)
        .filter(Seizure.user_id == user.id, Seizure.refund_id == refund_id, Seizure.status == 'REEMBOLSADO')
        .all()
    )
    if not _user_seizure_list:
        _session.close()
        return False
    
    for _seizure in _user_seizure_list:
        _seizure.status = 'RESGATADO'
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

def _get_upper_limit_date(interaction: discord.Interaction):
    _pattern: str = r'(?<=à )[0-9]{2}/[0-9]{2}'
    _string: str = interaction.message.content
    _match_str: str = regex.search(pattern=_pattern, string=_string).group(0)
    _upper_limit_date: datetime = _get_datetime_from_string(_match_str)
    
    return _upper_limit_date

class ConfirmRefundView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.custom_id = f'confirm_refund_persistant_view'
        
    @ui.button(label='Confirmar recebimento', style=discord.ButtonStyle.success, custom_id='confirm_refund_button')
    async def confirmar_recebimento(self, interaction: discord.Interaction, button: ui.Button):
        try:
            refund_id: int = _get_refund_id(interaction=interaction)
        except Exception as e:
            await interaction.response.send_message(content='Erro ao obter o ID do reembolso.', ephemeral=True)
            return
        
        is_refund_confirmed:bool = _add_refund_confirmation(user=interaction.user, refund_id=refund_id)
        if not is_refund_confirmed:
            await interaction.response.send_message(content='Você não está na lista ou já resgatou os valores', ephemeral=True)
            return
        
        upper_limit_date: datetime = _get_upper_limit_date(interaction=interaction)
        
        await interaction.message.edit(content=new_refund_message_content(refund_id=refund_id, upper_limit_date=upper_limit_date))
        await interaction.response.send_message(content='Recebimento confirmado!', ephemeral=True, delete_after=3)
   
    @ui.button(label='[SUP+] Finalizar pagamento', style=discord.ButtonStyle.danger, custom_id='finish_payments_button')
    async def finalizar_pagamento(self, interaction: discord.Interaction, button: ui.Button):
        await self.bot.get_user(interaction.user.id).send(content='oie')