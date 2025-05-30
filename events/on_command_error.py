import discord
from discord.ext import commands
from config import *

def setup_events(bot:commands.Bot):
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error):
        actual_error = getattr(error, 'original', error)

        if isinstance(actual_error, commands.MissingAnyRole):
            await bot.get_guild(interaction.guild_id).get_channel(interaction.channel_id).send(f'{interaction.user.mention} Você não tem permissão para usar o comando {interaction.command.name}!')
        elif isinstance(actual_error, discord.NotFound):
            await bot.get_guild(interaction.guild_id).get_channel(interaction.channel_id).send(f'{interaction.user.mention} A interação do comando {interaction.command.name} falhou por tempo esgotado! Experimente tentar novamente.')
        else:
            await bot.get_guild(interaction.guild_id).get_channel(interaction.channel_id).send(f'{interaction.user.mention} Erro ao executar o comando {interaction.command.name}!')
            log_error = actual_error if actual_error is not error else error
            await bot.get_guild(LogGuild).get_channel(LogChannel).send(f'<@{MentionID}>\nErro no comando {interaction.command.name} por {interaction.user.name}:\n{log_error}')