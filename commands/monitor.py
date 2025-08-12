import discord, aiohttp, io
from discord.ext import commands
from utils.ImageManager import get_image_url_from_message, get_monitor_image_file


def setup_commands(bot: commands.Bot):
    
    @bot.command(
        name='monitor',
        help='Coloca a imagem de uma mensagem mencionada na tela do monitor.'
    )
    async def televisao(ctx: commands.Context):
        
        if not ctx.message.reference:
            await ctx.reply(
                content='Putz! Não achei menção à uma mensagem...',
                delete_after=10
            )
            return
        
        try:
            referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except discord.NotFound:
            await ctx.reply("Ué, não consegui encontrar a mensagem original. Será que ela foi apagada?", delete_after=10)
            return

        image_urls = get_image_url_from_message(message=referenced_message)
        
        if not image_urls:
            await ctx.reply(
                content='Putz! Não achei nenhuma imagem na mensagem que você selecionou...',
                delete_after=10
            )
            return

        image_url = image_urls[0] if isinstance(image_urls, list) else image_urls
        
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    await ctx.reply('Não consegui baixar a imagem da mensagem selecionada...', delete_after=10)
                    return
                image_bytes = io.BytesIO(await response.read())

        image_file = get_monitor_image_file(reference_image=image_bytes)
        
        await ctx.send(file=image_file, reference=ctx.message)