from PIL import Image
import numpy as np

def _find_coeffs(source_coords, target_coords):
    matrix = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])
    
    A = np.array(matrix, dtype=np.float64)
    B = np.array(source_coords).reshape(8)
    
    res = np.linalg.solve(A, B)
    return res.tolist()

reference_image = Image.open('C:/Users/whosm/Downloads/bot junino.png').convert('RGBA')
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

imagem_final = Image.alpha_composite(tv_image, distorted_image)

imagem_final.save('teste-perspectiva-final.png', format='PNG')