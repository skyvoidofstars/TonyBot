import discord, io
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from config import seizure_value

def _find_coeffs(source_coords, target_coords):
    matrix = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])
    
    A = np.array(matrix, dtype=np.float64)
    B = np.array(source_coords).reshape(8)
    
    res = np.linalg.solve(A, B)
    return res.tolist()

def get_forbidden_message_image(interaction: discord.Interaction) -> discord.File:
    
    first_name: str = interaction.user.display_name.split(sep=' ')[0]
    
    text: str = f'eu sou lerda\nmas não sou\nburra, {first_name}'

    image: Image = Image.open('assets/response_unauthorized.png').convert('RGBA')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(
        font='assets/arial.ttf',
        encoding='unic',
        size=22)
    draw.text(
        xy=(155, 50),
        text=text,
        fill='black',
        anchor='mm',
        align='center',
        font=font)

    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    
    file: discord.File = discord.File(fp=output, filename='lerda_mas_nao_burra.png')
    
    return file

def get_tv_image_file(reference_image: io.BytesIO):
    reference_image = Image.open(reference_image).convert('RGBA')
    tv_image = Image.open('assets/watching_tv.png').convert('RGBA')

    width, height = reference_image.size
    cantos_origem = [(0, 0), (width, 0), (width, height), (0, height)]

    corners: list[tuple[int, int]] = [
        (1351, 406), # -> Canto Superior Esquerdo
        (1876, 330), # -> Canto Superior Direito
        (1869, 686), # -> Canto Inferior Direito
        (1344, 682) # -> Canto Inferior Esquerdo
    ]

    coeffs = _find_coeffs(cantos_origem, corners)

    distorted_image = reference_image.transform(
        size=tv_image.size,
        method=Image.Transform.PERSPECTIVE,
        data=coeffs,
        resample=Image.Resampling.BICUBIC, 
    )

    output_buffer = io.BytesIO()
    imagem_final = Image.alpha_composite(tv_image, distorted_image)
    imagem_final.save(output_buffer, format='PNG')
    output_buffer.seek(0)

    image_file: discord.File = discord.File(fp=output_buffer, filename='tv_mec.png')
    
    return image_file

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
