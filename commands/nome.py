import discord
from discord.ext import commands
from db import NewSession, User

def setup_commands(bot:commands.Bot):
    @bot.command(name='nome', description='Altera o nome do personagem')
    async def nome(ctx:discord.ext.commands.Context, *, name:str):
        session = NewSession()
        user = session.query(User).filter_by(user_id=ctx.author.id).first()
        if not user:
            session.close()
            await ctx.message.delete()
            await ctx.send(f'{ctx.author.mention} Você não está cadastrado no sistema!')
            return
        user.user_character_name = name
        session.commit()
        session.close()
        await ctx.message.delete()
        await ctx.send(f'{ctx.author.mention} Nome alterado para `{name}` com sucesso!')