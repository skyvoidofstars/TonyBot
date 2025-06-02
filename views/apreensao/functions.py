import discord, textwrap, io
from discord.ext import commands
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime
from db import User, Seizure, SeizureRefund, _new_session
from config import brasilia_tz, embed_width, seizure_channel_id, aux_db_channel, seizure_value
from utils.ImageManager import get_image_url_from_message
from utils.PersistantViewManager import update_new_seizure_message
from views.apreensao.SeizureCancel import SeizureCancelView

def _deleve_invalid_entries(session: Session, user_id: int, seizure_id: int):
    try:
        _invalid_entries: Seizure = (
            session.query(Seizure)
            .filter(
                Seizure.seizure_id != seizure_id,
                Seizure.status == 'PENDENTE',
                Seizure.user_id == user_id
            )
        )
        
        if _invalid_entries:
            for entry in _invalid_entries:
                session.delete(entry)
        session.commit()
        
    except Exception as e:
        print(f"Erro ao deletar entradas inválidas: {e}")
        session.rollback()
    finally:
        session.close()

async def _save_image_to_aux_db(bot:commands.Bot, message: discord.Message) -> discord.Message:
    _original_file: discord.Attachment = message.attachments[0]
    _file_bytes: bytes = await _original_file.read()
    
    _file: discord.File = discord.File(
        filename=_original_file.filename,
        fp=io.BytesIO(_file_bytes)
    )
    
    _message: discord.Message = await bot.get_guild(message.guild.id).get_channel(aux_db_channel).send(
        content=f'Imagem enviada por {message.author.name}',
        file=_file
    )
    
    return _message

def _create_embed(seizure: Seizure, message: discord.Message) -> discord.Embed:
    
    _employee: str = seizure.user.user_character_name.ljust(embed_width)
    _icon_url: str = message.author.display_avatar.url
    _officer_name: str = seizure.officer_name
    _officer_badge: str = seizure.officer_badge
    _observations: str | None = seizure.observations
    _image_url: str = seizure.image_url
    
    _embed: discord.Embed = discord.Embed(
        title = 'Registro de apreensão',
        color = discord.Color.blue(),
        timestamp = datetime.now(brasilia_tz)
    )
    
    _embed.set_author(name=message.author.name, icon_url=_icon_url)
    
    _embed.add_field(name='👤 Funcionário', value=f'```\n{_employee}\n```', inline=False)
    _embed.add_field(name='👮 Oficial', value=f'```\n{_officer_name}\n```', inline=True)
    _embed.add_field(name='⭐ Distintivo', value=f'```\n{_officer_badge}\n```', inline=True)
    
    if _observations:
        _embed.add_field(name='📝 Observações', value=f'```\n{'\n'.join(textwrap.wrap(_observations, width=embed_width))}\n```', inline=False)
    
    _embed.add_field(name='📷 Imagem da apreensão', value=f'[Ver imagem no tamanho original]({_image_url})', inline=False)
    
    _embed.set_image(url=_image_url)
    
    _embed.set_footer(text=f'ID da apreensão: {seizure.seizure_id}')

    return _embed

async def finish_seizure(bot: commands.Bot, session: Session, seizure: Seizure, original_message: discord.Message) -> None:
    
    _deleve_invalid_entries(session=session, user_id=seizure.user_id, seizure_id=seizure.seizure_id)
    
    new_message: discord.Message = await _save_image_to_aux_db(bot=bot, message=original_message)
    image_url: str = get_image_url_from_message(new_message)
    
    seizure.image_url = image_url
    seizure.status = 'CRIADO'
    session.add(seizure)
    session.commit()
    session.refresh(seizure)
    
    embed: discord.Embed = _create_embed(seizure=seizure, message=original_message)
    
    confirmation_message: discord.Message = await bot.get_guild(original_message.guild.id).get_channel(seizure_channel_id).send(embed=embed, view=SeizureCancelView(bot=bot))
    
    seizure.message_id = confirmation_message.id
    session.add(seizure)
    session.commit()
    session.close()
    
    await original_message.delete()
    try:
        await update_new_seizure_message(bot=bot)
    except Exception as e:
        print(f"Erro ao chamar update_new_seizure_message em finish_seizure: {e}")
        
def _get_refund_information(refund_id: int) -> str:
    _session: Session = _new_session()
    _refund_list: list[tuple[str, int, datetime]] = (
        _session.query(
            User.user_character_name,
            (func.count(Seizure.refund_id) * seizure_value).label('total_value'),
            func.max(Seizure.redeemed_at)
        )
        .join(User, User.user_id == Seizure.user_id)
        .filter(Seizure.refund_id == refund_id)
        .group_by(User.user_character_name)
        .order_by(User.user_character_name)
        .all()
    )

    _refund_values: list[tuple[int, int]] = (
        _session.query(SeizureRefund.total_value, func.coalesce(SeizureRefund.redeemed_value, 0))
        .filter(SeizureRefund.refund_id == refund_id)
        .first()
    )

    _total_value_int: int = _refund_values[0]
    _total_value: str = f'$ {_total_value_int:,}'.replace(',', '.')
    _redeemed_value_int: int = _refund_values[1]
    _redeemed_value: str = f'$ {_redeemed_value_int:,}'.replace(',', '.')
    _remaining_value_int: int = _total_value_int - _redeemed_value_int
    _remaining_value: str = f'$ {_remaining_value_int:,}'.replace(',', '.')


    _session.close()
    
    _refund_information: str = f'# {'Nome do funcionário'.center(29, ' ')} {'Valor'.center(10, ' ')}  Data e hora da retirada\n'
    for _row in _refund_list:
        _user = _row[0]
        _value = _row[1]
        _redeemed_at = _row[2]
        _prefix: str = ''
        _emoji: str = ''
        if _redeemed_at:
            _prefix = '+'
            _emoji = '✅'
            _date_if_redeemed: str = _redeemed_at.strftime('%d/%m/%Y às %H:%M:%S')
        else:
            _prefix = '-'
            _emoji = '⏳'
            _date_if_redeemed: str = 'PENDENTE'
        _formatted_value: str = f'{_value:,}'.replace(',','.')
        _refund_information += f'{_prefix} {_emoji} {_user.ljust(25)[:25]} | $ {_formatted_value.rjust(6)} | {_date_if_redeemed}\n'

    _refund_information += (
        f'\n'
        f'Valor total: {_total_value}\n'
        f'Valor resgatado: {_redeemed_value} {f'(restam {_remaining_value})' if _remaining_value_int > 0 else ''}\n'
    )

    _refund_information = _refund_information.strip()
    
    return _refund_information

def _get_pendent_users_mention(refund_id: int) -> str:
    
    session: Session = _new_session()
    seizure_user_ids_list: list[int] = (
        session.query(Seizure.user_id)
        .join(User, User.user_id == Seizure.user_id)
        .filter(Seizure.status == 'REEMBOLSADO', Seizure.refund_id == refund_id)
        .order_by(User.user_character_name)
        .distinct()
        .all()
    )

    _mentions = ' '
    for _user in seizure_user_ids_list:
        _mentions += f'<@{_user[0]}> '
        
    return _mentions
        
def new_refund_message_content(upper_limit_date: datetime, refund_id: int):
    
    session: Session = _new_session()
    _user_id: int = session.query(SeizureRefund.created_by).filter(SeizureRefund.refund_id == refund_id).scalar()
    
    lower_limit_date: datetime = (
        session.query(func.min(Seizure.created_at).label(''))
        .filter(Seizure.refund_id == refund_id)
        .scalar()
    )
    session.close()
    
    refund_info: str = _get_refund_information(refund_id=refund_id)
        
    lower_limit_date = lower_limit_date.strftime(format='%d/%m')
    upper_limit_date = upper_limit_date.strftime(format='%d/%m')
    
    mention_users: str = _get_pendent_users_mention(refund_id=refund_id)
    
    message_content: str = (
            f'## Período: {lower_limit_date} à {upper_limit_date}\n\n'
            f'```diff\n{refund_info}\n```\n'
            f'Reembolsos gerados por <@{_user_id}> sob o ID {refund_id}\n\n'
            f'||{mention_users}||\n\n'
            f'Para confirmar a retirada do valor do baú, clique no botão abaixo'
        )
    
    return message_content