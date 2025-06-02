import discord, regex
from sqlalchemy.orm import Session
from datetime import datetime
from db import User, _new_session
from config import brasilia_tz

def _extract_character_name(display_name: str) -> str:
    match: regex.Match = regex.match(r"^([\p{L}\s]+\p{L})", display_name)
    if match:
        return match.group(1)
    return display_name.split('|')[0].strip()

def get_or_create_user(discord_user: discord.User) -> User:
    session = _new_session()
    user: User = session.query(User).filter_by(user_id=discord_user.id).first()

    if not user:
        character_name: str = _extract_character_name(discord_user.display_name)

        user: User = User(
            user_id=discord_user.id,
            username=discord_user.name,
            user_display_name=discord_user.display_name,
            user_character_name=character_name,
            created_at=datetime.now(brasilia_tz)
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        session.close()

    return user