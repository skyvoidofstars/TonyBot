import discord
from discord.ext import commands
from config import *

def setup_events(bot:commands.Bot):
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error):
        match True:
            case isinstance(error, commands.MissingAnyRole):
                await bot.get_guild(interaction.guild_id).get_channel(interaction.channel_id).send(f'{interaction.user.mention} Você não tem permissão para usar o comando {interaction.command.name}!')
            case isinstance(error, discord.NotFound):
                await bot.get_guild(interaction.guild_id).get_channel(interaction.channel_id).send(f'{interaction.user.mention} A interação do comando {interaction.command.name} falhou por tempo esgotado! Experimente tentar novamente.')
            case _:
                await bot.get_guild(interaction.guild_id).get_channel(interaction.channel_id).send(f'{interaction.user.mention} Erro ao executar o comando {interaction.command.name}!')
                await bot.get_guild(LogGuild).get_channel(LogChannel).send(f'<@{MentionID}>\nErro no comando {interaction.command.name} por {interaction.user.name}:\n{error}')
