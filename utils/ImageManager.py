import discord, io
from PIL import Image, ImageDraw, ImageFont
from config import seizure_value


def get_image_url_from_message(message: discord.Message) -> str | None:
    if not message.attachments:
        return None

    _urls: list[str] = []

    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith('image/'):
            _urls.append(attachment.url)
        elif attachment.height is not None and attachment.width is not None:
            common_image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
            if attachment.filename.lower().endswith(common_image_extensions):
                _urls.append(attachment.url)
    return _urls


def get_seizure_report_image(dates_interval: str, tow_count: int) -> discord.File:
    font_size: int = 140
    stroke_width: int = 3

    unit_value: str = f'{f'{seizure_value:,}'.rjust(10)}'.replace(',', '.') + ',00'
    total_value: str = f'{f'{seizure_value*tow_count:,}'.rjust(10)}'.replace(',', '.') + ',00'
    tow_count_text: str = f'{tow_count} reboques'

    img: Image = Image.open('assets/report_template.png').convert('RGBA')
    draw = ImageDraw.Draw(img)

    try:
        font: ImageFont = ImageFont.truetype(
            'assets/GlacialIndifference-Regular.otf', size=font_size
        )
    except IOError:
        print(f'Fonte não encontrada. Usando fonte padrão da Pillow.')
        try:
            font: ImageFont = ImageFont.load_default(size=font_size)
        except AttributeError:
            font: ImageFont = ImageFont.load_default()

    draw.text(
            xy=(1684, 1424),
            text=dates_interval,
            fill='#1c155b',
            font=font,
            anchor='mm',
            align='center',
            stroke_width=stroke_width
        )
    draw.text(
        xy=(440, 2070),
        text='$',
        fill='#1c155b',
        font=font,
        anchor='ls',
        align='left',
        stroke_width=stroke_width
    )
    draw.text(
        xy=(1140, 2070),
        text=unit_value,
        fill='#1c155b',
        font=font,
        anchor='rs',
        align='right',
        stroke_width=stroke_width
    )
    draw.text(
        xy=(2300, 2000),
        text=tow_count_text,
        fill='#1c155b',
        font=font,
        anchor='mm',
        align='center',
        stroke_width=stroke_width
    )
    draw.text(
        xy=(1625, 2660),
        text='$',
        fill='#1c155b',
        font=font,
        anchor='ls',
        align='left',
        stroke_width=stroke_width
    )
    draw.text(
        xy=(2950, 2660),
        text=total_value,
        fill='#1c155b',
        font=font,
        anchor='rs',
        align='right',
        stroke_width=stroke_width
    )

    output_buffer = io.BytesIO()
    img.save(output_buffer, format='PNG')
    output_buffer.seek(0)
    discord_file = discord.File(output_buffer, filename='seizure_report.png')

    return discord_file
