import discord
from discord import ui
from discord.ext import commands

class SupervisionMessageModal(ui.Modal, title='💬 Nova mensagem privada'):
    message_title: ui.TextInput = ui.TextInput(
        label='🎯 Título',
        placeholder='Comunicado importante',
        required=False,
        style=discord.TextStyle.short,
        max_length=60,
    )
    message_content: ui.TextInput = ui.TextInput(
        label='💬 Mensagem',
        placeholder='Olá, Fulano! Tudo bem?...',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=2000,
    )
    message_footer: ui.TextInput = ui.TextInput(
        label='📍 Rodapé (automático se vazio)',
        placeholder='Atenciosamente\nDireção Los Santos Customs',
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=300,
    )

    def __init__(self, bot: commands.Bot, user: discord.User):
        super().__init__(timeout=None)
        self.bot: commands.Bot = bot
        self.user: discord.User = user

    async def on_submit(self, interaction: discord.Interaction):
        message_title: str = self.message_title.value
        message_content: str = self.message_content.value
        message_footer: str = self.message_footer.value
        
        message_title = f'# {message_title}\n\n' if message_title else ''
        
        if not message_footer:
            message_footer = 'Atenciosamente\nDireção Los Santos Customs'
        
        message_footer = (
            '\n'.join([f'_{linha}_' for linha in message_footer.splitlines()]) +
            f'\n-# Não responda esta mensagem, em caso de dúvidas entre em contato com a direção'
        )
        
        try:
            await self.user.send(
                content= (
                    f'{message_title}' +
                    f'{message_content}\n\n' +
                    f'{message_footer}'
                )
            )
            
            await interaction.response.send_message(
                content='Mensagem enviada com sucesso!'
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                content='Não foi possível enviar a mensagem. O usuário bloqueou mensagens diretas.'
            )
        except Exception as e:
            await interaction.response.send_message(
                content=f'Ocorreu um erro ao enviar a mensagem. Tente novamente mais tarde.\n\n{e}'
            )
        return