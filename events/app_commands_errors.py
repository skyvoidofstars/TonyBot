import discord
from config import *

def setup_events(bot:discord.ext.commands.Bot):
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error):
        if isinstance(error, discord.app_commands.MissingAnyRole):
            await bot.get_guild(interaction.guild_id).get_channel(interaction.channel_id).send(f'{interaction.user.mention} Você não tem permissão para usar o comando {interaction.command.name}!')
        else:
            await bot.get_guild(interaction.guild_id).get_channel(interaction.channel_id).send(f'{interaction.user.mention} Erro ao executar o comando!\n{error}')
            await bot.get_guild(LogGuild).get_channel(LogChannel).send(f'<@129620949090697216>\nErro no comando {interaction.command.name} por {interaction.user.name}:\n{error}')
