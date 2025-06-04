import discord
from discord import ui
from discord.ext import commands
from views.apreensao.SeizurePopup import SeizureView
from config import seizure_channel_id, refund_channel_id


def _get_help_message(bot: commands.Bot) -> list[str]:
    _seizure_channel = bot.get_channel(seizure_channel_id).mention
    _refund_channel = bot.get_channel(seizure_channel_id).mention
    _help_message: str = [
        (
            "# Utilizando o registro de apreensões\n"
            "**Registrar uma apreensão consiste em alguns pasoss básicos:**\n"
            '- Clicar em "Nova apreensão"\n'
            "- Inserir o nome do oficial e o número do distintivo\n"
            "- Enviar a foto no canal\n\n"
            "De forma **automática**, o bot pegará a foto e anexará no seu registro\n"
        ),
        (
            "## 1. Registrando a apreensão\n"
            f"- Vá ao canal {_seizure_channel} e clique no botão de **nova apreensão**\n"
            "\nhttps://media.discordapp.net/attachments/826170907735228436/1379172378881556570/image.png?ex=683f45de&is=683df45e&hm=8db179e66fe174bf52af15a5f7838df4740283b8a26cab7c2693fdbb25fa0aae&=&format=webp&quality=lossless"
        ),
        (
            "- O bot mostrará uma janela para o preencimento de informações\n"
            "- Insira:\n"
            " - O **nome** do oficial\n"
            " - O **número do distintivo**\n"
            "\nhttps://media.discordapp.net/attachments/826170907735228436/1379173004289900715/image.png?ex=683f4674&is=683df4f4&hm=91ada4c6191f066d7f27d518dda2911f8e2927b21f10cc3260bdd4459e5ff98a&=&format=webp&quality=lossless"
        ),
        (
            "- **Envie a imagem** no chat\n\n"
            f"Dica: utilize **Windows + Shift + S** para capturar a imagem da apreensão, depois, só dar **Ctrl + V** no {_seizure_channel}\n\n"
            "O bot pegará sua imagem, anexará na apreensão e o registro será **concluído**\n"
            "\nhttps://media.discordapp.net/attachments/826170907735228436/1379176526150635700/image.png?ex=683f49bb&is=683df83b&hm=08c248c773bb77a32ca6890970560bec64138d4b7c0b679ed63dee0cf681a921&=&format=webp&quality=lossless"
        ),
        (
            "**O registro aparecerá conforme o modelo abaixo**\n"
            "\nhttps://media.discordapp.net/attachments/826170907735228436/1379177016258985994/image.png?ex=683f4a30&is=683df8b0&hm=a5c5ed13cdc2422fc7165b84e9c8fa91a5d5e06e14f51919bd303b44cb2fa0fd&=&format=webp&quality=lossless"
        ),
        (
            "## 2. Cancelando o registro\n"
            "Caso precise cancelar seu registro de apreensão, clique no botão de cancelar\n"
            "**Essa ação é irreversível!**\n"
            "-# Somente você ou a supervisão+ pode cancelar seus registros\n"
            "\nhttps://media.discordapp.net/attachments/826170907735228436/1379178172851032094/image.png?ex=683f4b44&is=683df9c4&hm=9d0a81d0617165eed490092eeaaa35cef3d6a307539ab645b3fa5cd71fb82efa&=&format=webp&quality=lossless"
        ),
        (
            "## 3. Fechamento do período de apreensões\n"
            "Quando um fechamento é realizado, não será mais possível cancelar ele\n"
            "\nhttps://media.discordapp.net/attachments/826170907735228436/1379178763920609382/image.png?ex=683f4bd1&is=683dfa51&hm=95908cbb32a10ece438ae10e76d87c1071b9d787623bee88a95e570e7d05034d&=&format=webp&quality=lossless"
        ),
        (
            f"No canal de {_refund_channel} você poderá confirmar seus pagamentos\n"
            "\nhttps://media.discordapp.net/attachments/826170907735228436/1379180129091064009/image.png?ex=683f4d16&is=683dfb96&hm=835ee3af6794b523c9454b8e05d1957347d73c143140d3042378161fc8456bd8&=&format=webp&quality=lossless"
        ),
        (
            "Caso encontre dificuldades ou precise de ajuda, entre em contato com <@129620949090697216> ou algúem da supervisão+"
        ),
    ]

    return _help_message


class NewSeizureView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.custom_id = "new_seizure_persistent_button"

    @ui.button(
        label="Nova Apreensão",
        style=discord.ButtonStyle.success,
        custom_id="new_seizure_button",
    )
    async def new_seizure_button(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        modal = SeizureView(bot=self.bot)
        await interaction.response.send_modal(modal)

    @ui.button(
        label="Ajuda", style=discord.ButtonStyle.secondary, custom_id="help_button"
    )
    async def help_button(self, interaction: discord.Interaction, button: ui.Button):
        help_messages: list[str] = _get_help_message(self.bot)
        await interaction.response.send_message(
            content="Instruções enviadas!", ephemeral=True, delete_after=15
        )
        for _message in help_messages:
            await interaction.user.send(_message)
