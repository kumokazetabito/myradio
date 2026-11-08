"""Build the male02 animation data texture without changing the artwork.

White is nearer to the viewer. Coordinates follow the approved 1199x1312
illustration; this is a smooth deformation field, not visible character art.
"""
from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]


def build():
    pack = ROOT / 'character/male02'
    base = Image.open(pack / 'base.png').convert('RGBA')
    w, h = base.size
    # Rear hair is far; torso, head and headphones are progressively nearer.
    # Smooth fields keep facial patches attached to the same moving surface.
    fields = [
        (600, 1090, 435, 600, 0.65),  # broad torso / shoulders
        (604, 645, 225, 200, 0.64),   # neck / collar
        (604, 340, 335, 320, 0.77),   # head and front mane
        (607, 490, 215, 155, 0.86),   # face
        (352, 450, 82, 145, 0.68),   # headphones
        (847, 450, 82, 145, 0.68),
        (365, 170, 100, 115, 0.60),  # round lion ears
        (828, 170, 100, 115, 0.60),
    ]
    sw, sh = 300, 328
    pixels = []
    for sy in range(sh):
        y = (sy + .5) * h / sh
        for sx in range(sw):
            x = (sx + .5) * w / sw
            d = .24
            for cx, cy, rx, ry, near in fields:
                r2 = ((x-cx)/rx)**2 + ((y-cy)/ry)**2
                if r2 < 1:
                    # Smooth join with the rear hair, with a rounded front.
                    d = max(d, .24 + (near-.24) * (1-r2)**.65)
            pixels.append(round(d*255))
    depth = Image.new('L', (sw, sh)); depth.putdata(pixels)
    depth = depth.resize((w, h), Image.Resampling.BICUBIC)
    # Transparent pixels are far; antialiased contours remain soft.
    alpha = base.getchannel('A').filter(ImageFilter.GaussianBlur(1.2))
    from PIL import ImageChops
    depth = ImageChops.multiply(depth, alpha)
    depth.save(pack / 'depth.png')
    print(f'Built male02 depth: {w}x{h}')


if __name__ == '__main__':
    build()
