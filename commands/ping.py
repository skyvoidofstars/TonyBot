import discord
from discord.ext import commands


def setup_commands(bot: commands.Bot):
    @bot.tree.command(name="ping", description="Mostra o ping do bot")
    async def ping(interaction: discord.Interaction):
        latency = round(bot.latency * 1000)
        await interaction.response.send_message(
            f"Pong! {latency}ms", ephemeral=True, delete_after=5
        )
