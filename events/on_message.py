import discord
from discord.ext import commands
from sqlalchemy import desc
from sqlalchemy.orm import Session
from config import seizure_channel_id
from db import User, Seizure, _new_session
from utils.UserManager import get_or_create_user
from utils.ImageManager import get_image_url_from_message
from views.apreensao.functions import finish_seizure

def setup_events(bot: commands.Bot):

    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        match message.channel.id:
            # Apreensão
            case seizure_channel_id:
                image_url = get_image_url_from_message(message=message)
                if image_url:
                    session: Session = _new_session()
                    user: User = get_or_create_user(discord_user=message.author)
                    seizure: Seizure | None = session.query(Seizure).filter_by(user_id=user.user_id, status='PENDENTE').order_by(desc(Seizure.created_at)).first()
                    if seizure:
                        await finish_seizure(bot=bot, session=session, seizure=seizure, original_message=message)
                    session.close()
                
        await bot.process_commands(message)
