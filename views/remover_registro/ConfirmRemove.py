import discord
from discord.ext import commands
from sqlalchemy.orm import Session
from db import Chest, Log
from config import *
from datetime import datetime

class ConfirmRemove(discord.ui.View):
    def __init__(self, bot:commands.Bot, session: Session, interaction:discord.Interaction, chest:Chest):
        super().__init__(timeout=15)
        self.bot: commands.Bot = bot
        self.session: Session = session
        self.interaction: discord.Interaction = interaction
        self.chest: Chest = chest
        self.user: discord.User = interaction.user
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message(f'{interaction.user.mention} Você não pode cancelar essa operação!')
            return
        await interaction.message.delete()
        await interaction.response.send_message("Operação cancelada.", ephemeral=True,  delete_after=5)
        self.session.close()
        self.stop()

    @discord.ui.button(label="Remover registro", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user != self.user:
                await interaction.response.send_message(f'{interaction.user.mention} Você não pode remover esse registro!')
                return
            if self.chest.message_id:
                OriginalMsg = await self.bot.get_channel(self.chest.channel_id).fetch_message(self.chest.message_id)
                await OriginalMsg.delete()
            self.session.delete(self.chest)
            self.session.commit()
            await interaction.message.delete()
            
            log = Log(
                guild=self.chest.guild_id,
                user_id=self.user.id,
                description=f'Registro de {'reabastecimento ' if self.chest.quantity > 0 else 'retirada'} de {self.chest.quantity}x {self.chest.item.item_name} de {self.chest.user.user_character_name} removido por {self.user.name}',
                timestamp=datetime.now(brasilia_tz)
            )
            
            self.session.add(log)
            self.session.commit()
            
            await self.bot.get_guild(interaction.guild.id).get_channel(LogChannel).send(content=f'{self.user.mention} removeu o registro de {self.chest.user.user_character_name} de {self.chest.quantity} un. de {self.chest.item.item_name}.{' Observação da transação: ' + self.chest.observations if self.chest.observations else ''}\nID da transação removida: {self.chest.chest_id}')
            
        except Exception as e:
            await interaction.response.send_message(f"Erro ao remover registro: {e}", ephemeral=True)
            await self.bot.get_guild(interaction.guild.id).get_channel(LogChannel).send(f'<@{MentionID}>\nErro no comando remover_registro (botões) por {interaction.user.name}:\n{e}')
        finally:
            self.session.close()
            self.stop()

    async def on_timeout(self):
        print(f"View para a interação {self.interaction.id} expirou. Tentando deletar a mensagem original.")
        try:
            await self.interaction.delete_original_response()
        except discord.HTTPException as e:
            print(f"Falha ao deletar a mensagem original da interação no timeout: {e}")


