from PIL import Image, ImageDraw, ImageFont

nome:str = 'fulano da silva'

first_name: str = nome.split(' ')[0]
text: str = f'teste de\nmensagem,\n {first_name}'

image: Image = Image.open('assets/response_unauthorized.png').convert('RGBA')
draw = ImageDraw.Draw(image)
font = ImageFont.load_default(size=16)
draw.text(
    xy=(155, 50),
    text=text,
    fill='black',
    anchor='mm',
    align='center',
    font=font)

image.save('sample-out-local.png')