import discord

class ConfirmRemoveView(discord.ui.View):
        def __init__(self, session, chest, user, bot):
            super().__init__(timeout=30)
            self.session = session
            self.chest = chest
            self.user = user
            self.bot = bot
        @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user != self.user:
                await interaction.response.send_message('Você não pode cancelar essa operação!', ephemeral=True, delete_after=5)
                return
            await interaction.message.delete()
            await interaction.response.send_message("Operação cancelada.", ephemeral=True,  delete_after=5)
            self.session.close()
            self.stop()

        @discord.ui.button(label="Remover registro", style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                if interaction.user != self.user:
                    await interaction.response.send_message('Você não pode remover esse registro!', ephemeral=True, delete_after=5)
                    return
                if self.chest.message_id:
                    OriginalMsg = await self.bot.get_channel(self.chest.channel_id).fetch_message(self.chest.message_id)
                    await OriginalMsg.delete()
                self.session.delete(self.chest)
                self.session.commit()
                await interaction.message.delete()
                await interaction.response.send_message("Registro removido com sucesso!", ephemeral=True, delete_after=5)
            except Exception as e:
                await interaction.response.send_message(f"Erro ao remover registro: {e}", ephemeral=True)
            finally:
                self.session.close()
                self.stop()