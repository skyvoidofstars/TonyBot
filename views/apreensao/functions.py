import discord, textwrap, io
from discord.ext import commands
from sqlalchemy.orm import Session
from datetime import datetime
from db import Seizure
from config import brasilia_tz, embed_width, seizure_channel_id, aux_db_channel
from utils.ImageManager import get_image_url_from_message
from views.apreensao.SeizureCancel import SeizureCancelView

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