# utils/PersistentViewManager.py
from sqlalchemy.orm import Session
from db import PersistentMessage, _new_session
from config import seizure_channel_id
from views.apreensao.NewSeizure import NewSeizureView #
import discord
from discord.ext import commands

async def update_new_seizure_message(bot: commands.Bot):
    session: Session = _new_session()
    view_key: str = 'new_seizure_persistent_button'

    persistent_message: PersistentMessage = (
        session.query(PersistentMessage)
        .filter_by(view_key=view_key)
        .first()
    )
    
    if persistent_message and persistent_message.message_id:
        try:
            message: discord.Message = await bot.get_channel(persistent_message.channel_id).fetch_message(persistent_message.message_id)
            await message.delete()
        except discord.NotFound:
            print(f'Mensagem persistente antiga ({persistent_message.message_id}) não encontrada. Será substituída.')
            session.close()
        except discord.HTTPException as e:
            print(f'Erro ao apagar mensagem persistente antiga: {e}')
            session.close()

    _content: str = '## Registre uma nova apreensão'
    new_message: discord.Message = await bot.get_channel(seizure_channel_id).send(content=_content, view=NewSeizureView(bot=bot))

    if persistent_message:
        persistent_message.message_id = new_message.id
        persistent_message.channel_id = new_message.channel.id
    else:
        persistent_message = PersistentMessage(
            view_key=view_key,
            message_id=new_message.id,
            channel_id = new_message.channel.id
        )
    
    session.add(persistent_message)
    session.commit()
    session.close()

async def refresh_or_create_new_seizure(bot: commands.Bot):
    session: Session = _new_session()
    view_key: str = 'new_seizure_persistent_button'
    
    persistent_message = (
        session.query(PersistentMessage)
        .filter_by(view_key=view_key)
        .first()
    )
    session.close()
    
    message_exists = False
    
    if persistent_message and persistent_message.message_id:
        try:
            message: discord.Message = await bot.get_channel(persistent_message.channel_id).fetch_message(persistent_message.message_id)
            message_exists = True
        except discord.NotFound:
            print(f'Mensagem persistente NewSeizureView (ID: {persistent_message.message_id}) não encontrada no Discord. Será recriada.')
        except discord.HTTPException as e:
            print(f'Erro ao buscar mensagem persistente: {e}')
    
    if not message_exists:
        await update_new_seizure_message(bot)