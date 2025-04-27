import discord
from discord.ext import commands
from config import *

def setup_commands(bot: commands.Bot):
    @bot.command(name='apagar', description='Apaga a mensagem mencionada e a própria do comando.')
    async def apagar(ctx:discord.ext.commands.Context, id:int):
        await ctx.message.delete()
        if not any(role.id in AllowedRoles for role in ctx.author.roles):
            return
        if id:
            try:
                msg = await ctx.channel.fetch_message(id)
                await msg.delete()
                print(f'Mensagem apagada: {id} por {ctx.author.name}')
            except Exception as e:
                await print('Não foi possível encontrar a mensagem mencionada.')
