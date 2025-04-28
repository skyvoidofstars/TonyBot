import discord
from db import Chest
from config import *
from datetime import datetime

class ConfirmRemoveView(discord.ui.View):
        def __init__(self, session, chest, user, bot, entry:Chest):
            super().__init__(timeout=30)
            self.session = session
            self.chest = chest
            self.user = user
            self.bot = bot
            self.entry = entry
        @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user != self.user:
                await interaction.response.send_message('Você não pode cancelar essa operação!')
                return
            await interaction.message.delete()
            await interaction.response.send_message("Operação cancelada.", ephemeral=True,  delete_after=5)
            self.session.close()
            self.stop()

        @discord.ui.button(label="Remover registro", style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                if interaction.user != self.user:
                    await interaction.response.send_message('Você não pode remover esse registro!')
                    return
                if self.chest.message_id:
                    OriginalMsg = await self.bot.get_channel(self.chest.channel_id).fetch_message(self.chest.message_id)
                    await OriginalMsg.delete()
                self.session.delete(self.chest)
                self.session.commit()
                await interaction.message.delete()
                await interaction.response.send_message("Registro removido com sucesso!", ephemeral=True, delete_after=5)
                embed = discord.Embed(
                    title='🗑️ Registro removido!',
                    color=discord.Color.green()
                )
                
                embed.set_author(name=self.user.name, icon_url=self.user.display_avatar.url)
                
                embed.add_field(name='🎯 ID', value=f'```\n{self.chest.id}\n```', inline=True)
                embed.add_field(name='👤 Funcionário', value=f'```\n{self.chest.getUser.user_character_name}\n```', inline=False)
                embed.add_field(name='📦 Item', value=f'```\n{self.chest.item}\n```', inline=True)
                embed.add_field(name='🔢 Quantidade', value=f'```\n{abs(self.chest.quantity) if self.chest.item != "Dinheiro" else "$ " + str(abs(self.chest.quantity))}\n```', inline=True)
                embed.add_field(name='🪪 Removido por', value=f'{self.user.mention}', inline=False)
                
                embed.timestamp = datetime.now(brasilia_tz)
                
                await self.bot.get_guild(LogGuild).get_channel(LogChannel).send(embed=embed)
                
            except Exception as e:
                await interaction.response.send_message(f"Erro ao remover registro: {e}", ephemeral=True)
            finally:
                self.session.close()
                self.stop()