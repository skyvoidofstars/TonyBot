import discord, textwrap, io
from PIL import Image, ImageFile
from discord.ext import commands
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime
from db import User, Seizure, SeizureRefund, _new_session
from config import (
    brasilia_tz,
    embed_width,
    seizure_channel_id,
    aux_db_channel,
    seizure_value,
)
from utils.ImageManager import get_image_url_from_message
from utils.PersistantViewManager import update_new_seizure_message
from utils.ANSI import Colors
from views.apreensao.SeizureCancel import SeizureCancelView


def _deleve_invalid_entries(session: Session, user_id: int, seizure_id: int):
    try:
        _invalid_entries: Seizure = session.query(Seizure).filter(
            Seizure.seizure_id != seizure_id,
            Seizure.status == 'PENDENTE',
            Seizure.user_id == user_id,
        )

        if _invalid_entries:
            for entry in _invalid_entries:
                session.delete(entry)
        session.commit()

    except Exception as e:
        print(f'Erro ao deletar entradas inválidas: {e}')
        session.rollback()
    finally:
        session.close()


def _crop_image_as_square(img: bytes) -> bytes:
    try:
        img: ImageFile = Image.open(io.BytesIO(img))
        width, height = img.size
        crop_size = min(width, height)
        _left = (width - crop_size) / 2
        _top = (height - crop_size) / 2
        _right = (width + crop_size) / 2
        _bottom = (height + crop_size) / 2

        _cropped_img = img.crop((_left, _top, _right, _bottom))

        if _cropped_img.width > 500:
            _resample_filter = Image.Resampling.LANCZOS
        else:
            _resample_filter = Image.Resampling.BICUBIC

        resized_img = _cropped_img.resize((500, 500), resample=_resample_filter)

        _cropped_image_buffer = io.BytesIO()
        resized_img.save(_cropped_image_buffer, format=img.format or 'PNG')
        _cropped_image_buffer.seek(0)
        return _cropped_image_buffer.getvalue()

    except Exception as e:
        print(f'Erro ao cortar imagem: {e}')
        return None


async def _save_image_to_aux_db(
    bot: commands.Bot, message: discord.Message
) -> discord.Message:
    _original_file: discord.Attachment = message.attachments[0]
    _file_bytes: bytes = await _original_file.read()
    _cropped_file_bytes: bytes = _crop_image_as_square(img=_file_bytes)

    _file: discord.File = discord.File(
        filename=_original_file.filename, fp=io.BytesIO(_file_bytes)
    )
    _cropped_file: discord.File = discord.File(
        filename=f'cropped_{_original_file.filename}',
        fp=io.BytesIO(_cropped_file_bytes),
    )

    _files: list[discord.File] = [_file, _cropped_file]

    _message: discord.Message = (
        await bot.get_guild(message.guild.id)
        .get_channel(aux_db_channel)
        .send(content=f'Imagem enviada por {message.author.name}', files=_files)
    )

    return _message


def _create_embed(seizure: Seizure, message: discord.Message) -> discord.Embed:
    _employee: str = seizure.user.user_character_name.ljust(embed_width)
    _icon_url: str = message.author.display_avatar.url
    _officer_name: str = seizure.officer_name
    _officer_badge: str = seizure.officer_badge
    _observations: str | None = seizure.observations
    _image_url: str = seizure.image_url
    _cropped_image_url: str = seizure.cropped_image_url

    _embed: discord.Embed = discord.Embed(
        title='Registro de apreensão',
        color=discord.Color.blue(),
        timestamp=datetime.now(brasilia_tz),
    )

    _embed.set_author(name=message.author.name, icon_url=_icon_url)

    _embed.add_field(
        name='👤 Funcionário', value=f'```\n{_employee}\n```', inline=False
    )
    _embed.add_field(name='👮 Oficial', value=f'```\n{_officer_name}\n```', inline=True)
    _embed.add_field(
        name='⭐ Distintivo', value=f'```\n{_officer_badge}\n```', inline=True
    )

    if _observations:
        _embed.add_field(
            name='📝 Observações',
            value=f'```\n{'\n'.join(textwrap.wrap(_observations, width=embed_width))}\n```',
            inline=False,
        )

    _embed.add_field(
        name='📷 Imagem da apreensão',
        value=f'[Ver imagem no tamanho original]({_image_url})',
        inline=False,
    )

    _embed.set_image(url=_cropped_image_url)

    _embed.set_footer(text=f'ID da apreensão: {seizure.seizure_id}')

    return _embed


async def finish_seizure(
    bot: commands.Bot,
    session: Session,
    seizure: Seizure,
    original_message: discord.Message,
) -> None:
    _deleve_invalid_entries(
        session=session, user_id=seizure.user_id, seizure_id=seizure.seizure_id
    )

    new_message: discord.Message = await _save_image_to_aux_db(
        bot=bot, message=original_message
    )
    image_url, cropped_image_url = get_image_url_from_message(new_message)

    seizure.image_url = image_url
    seizure.cropped_image_url = cropped_image_url
    seizure.status = 'CRIADO'
    session.add(seizure)
    session.commit()
    session.refresh(seizure)

    embed: discord.Embed = _create_embed(seizure=seizure, message=original_message)

    confirmation_message: discord.Message = (
        await bot.get_guild(original_message.guild.id)
        .get_channel(seizure_channel_id)
        .send(embed=embed, view=SeizureCancelView(bot=bot))
    )

    seizure.message_id = confirmation_message.id
    session.add(seizure)
    session.commit()
    session.close()

    await original_message.delete()
    try:
        await update_new_seizure_message(bot=bot)
    except Exception as e:
        print(f'Erro ao chamar update_new_seizure_message em finish_seizure: {e}')


def _get_refund_information(refund_id: int, refund_finishing: bool) -> str:
    _session: Session = _new_session()
    _refund_list: list[tuple[str, int, datetime]] = (
        _session.query(
            User.user_character_name,
            (func.count(Seizure.refund_id) * seizure_value).label('total_value'),
            func.max(Seizure.redeemed_at),
        )
        .join(User, User.user_id == Seizure.user_id)
        .filter(Seizure.refund_id == refund_id)
        .group_by(User.user_character_name)
        .order_by(User.user_character_name)
        .all()
    )

    _refund_values: list[tuple[int, int]] = (
        _session.query(
            SeizureRefund.total_value, func.coalesce(SeizureRefund.redeemed_value, 0)
        )
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

    _refund_information: str = (
        # f'{Colors.BLUE}{'_' * embed_width}{Colors.END}\n'
        f'{Colors.BLUE}|{'FUNCIONÁRIO'.center(26, ' ')}|{'VALOR'.center(11, ' ')}|{'RETIRADA'.center(13)}|{Colors.END}\n'
    )
    for _row in _refund_list:
        _user = _row[0]
        _value = _row[1]
        _redeemed_at = _row[2]
        _ansi_prefix: str = ''
        if _redeemed_at:
            _ansi_prefix = Colors.GREEN
            _date_if_redeemed: str = _redeemed_at.strftime('%d/%m %H:%M')
        else:
            _ansi_prefix = Colors.YELLOW
            _date_if_redeemed: str = 'PENDENTE'
            if refund_finishing:
                _ansi_prefix = Colors.RED
                _date_if_redeemed = 'RETIDO'
        _formatted_value: str = f'{_value:,}'.replace(',', '.')
        _refund_information += f'{_ansi_prefix}| {_user.ljust(24)[:24]} | $ {_formatted_value.rjust(7)} | {_date_if_redeemed.ljust(12)}|{Colors.END}\n'

    _refund_information += (
        f'\n'
        f'Valor total: {_total_value}\n'
        f'Valor resgatado: {_redeemed_value} {f'(restam {_remaining_value})' if _remaining_value_int > 0 else ''}\n'
    )

    _refund_information = f'```ansi\n{_refund_information.strip()}\n```'

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

    _mentions: str = ''
    for _user in seizure_user_ids_list:
        _mentions += f'<@{_user[0]}> '

    if len(_mentions) == 0:
        return None

    _mentions = f'|| {_mentions} ||'

    return _mentions


async def new_refund_message_content(
    bot: commands.Bot,
    upper_limit_date: datetime,
    refund_id: int,
    refund_finishing: bool = False,
) -> list[str | None, discord.Embed]:
    session: Session = _new_session()
    _user_id: int = (
        session.query(SeizureRefund.created_by)
        .filter(SeizureRefund.refund_id == refund_id)
        .scalar()
    )
    _author_user: discord.User = await bot.fetch_user(_user_id)
    lower_limit_date: datetime = (
        session.query(func.min(Seizure.created_at).label(''))
        .filter(Seizure.refund_id == refund_id)
        .scalar()
    )
    session.close()

    lower_limit_date = lower_limit_date.strftime(format='%d/%m')
    upper_limit_date = upper_limit_date.strftime(format='%d/%m')

    message_content: str = _get_pendent_users_mention(refund_id=refund_id)

    message_embed: discord.Embed = discord.Embed(
        color=discord.Color.green() if not refund_finishing else discord.Color.red(),
        title=f'Reembolso de apreensões',
        timestamp=datetime.now(brasilia_tz),
    )
    refund_info: str = _get_refund_information(
        refund_id=refund_id, refund_finishing=refund_finishing
    )

    message_embed.set_author(
        name=_author_user.name, icon_url=_author_user.display_avatar.url
    )

    message_embed.add_field(
        name='📅 Período considerado',
        value=f'```\n{lower_limit_date} à {upper_limit_date}\n```',
        inline=False,
    )

    message_embed.add_field(name='💵 Reembolsos', value=refund_info, inline=False)

    message_embed.add_field(
        name='Para confirmar o recebimento, clique no botão abaixo',
        value='',
        inline=False,
    )

    message_embed.set_footer(text=f'ID do reembolso: {refund_id}')

    return message_content, message_embed
