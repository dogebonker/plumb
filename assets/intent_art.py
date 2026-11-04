"""Regenerate the README plate: python3 assets/intent_art.py (Pillow >=10.2).

Uses system Avenir Next / Menlo, falling back to DejaVu Sans / Sans Mono.
SVG keeps text editable and uses the same system-font stacks; no font is bundled.
"""
from hashlib import sha256
from html import escape
from itertools import pairwise
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
W, H = 960, 480
PAPER, INK, FAINT = '#f3efe4', '#252b28', '#c9c6b9'
GRAY, ORANGE, GREEN = '#696e64', '#d54b2c', '#52735e'


def font(size, bold=False, mono=False):
    candidates = ([('/System/Library/Fonts/Menlo.ttc', 0),
                   ('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 0)] if mono else
                  [('/System/Library/Fonts/Avenir Next.ttc', 0 if bold else 5),
                   ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 0)])
    for path, index in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size, index=index)
    raise RuntimeError('Install Avenir Next or DejaVu Sans to regenerate this plate.')


FONTS = {(size, bold, mono): font(size, bold, mono)
         for size, bold, mono in [(14, False, False), (15, False, False),
                                 (16, True, False), (20, True, False),
                                 (21, False, False), (21, False, True),
                                 (43, True, False)]}


class Plate:
    """One geometry source for the raster animation and editable SVG still."""
    def __init__(self):
        self.image = Image.new('RGB', (W, H), PAPER)
        self.draw = ImageDraw.Draw(self.image)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
                    '<title id="title">Plumb: carry intent into the code</title>',
                    '<desc id="desc">A plumb line connects module knowledge, a seven-day retention spec, the matching implementation, verification evidence, and a knowledge update. A return trace connects the update back to knowledge. Checks provide evidence, not a guarantee.</desc>',
                    f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']

    def line(self, points, color=INK, width=1):
        self.draw.line(points, fill=color, width=width)
        coords = ' '.join(f'{x},{y}' for x, y in points)
        self.svg.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{width}"/>')

    def circle(self, x, y, radius, color):
        self.draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}"/>')

    def polygon(self, points, color):
        self.draw.polygon(points, fill=color)
        coords = ' '.join(f'{x},{y}' for x, y in points)
        self.svg.append(f'<polygon points="{coords}" fill="{color}"/>')

    def text(self, x, y, text, size=21, color=INK, bold=False, mono=False):
        self.draw.text((x, y), text, font=FONTS[size, bold, mono], fill=color, anchor='lt')
        family = 'Menlo, DejaVu Sans Mono, monospace' if mono else 'Avenir Next, DejaVu Sans, sans-serif'
        self.svg.append(f'<text x="{x}" y="{y}" dominant-baseline="text-before-edge" font-family="{family}" font-size="{size}" font-weight="{700 if bold else 500}" fill="{color}">{escape(text)}</text>')


def render(progress):
    p = Plate()
    p.text(40, 24, 'P L U M B', 16, bold=True)
    p.text(660, 25, 'A SKILL FOR YOUR CODING AGENT', 14, GRAY)
    p.line([(40, 57), (920, 57)], INK)
    p.text(40, 77, 'Carry intent into the code.', 43, bold=True)
    p.text(41, 133, 'Read what lasts. Specify the change. Keep the result connected.', 21, GRAY)

    ys = [197, 240, 283, 326, 369]
    names = ['Module knowledge', 'Change spec', 'Implementation', 'Verification', 'Knowledge update']
    details = ['OKF · rules + source references', 'Retain audit records for 7 days',
               'retention_days = 7' if progress >= .54 else 'retention_days = 30',
               'Tests observed; evidence retained', 'Record what actually changed']
    # The fixed line is a reference, not a correctness score.
    p.line([(455, 177), (455, 401)], INK, 2)
    p.circle(455, 175, 4, INK)
    p.polygon([(444, 400), (466, 400), (455, 421)], ORANGE)
    for i, (y, name, detail) in enumerate(zip(ys, names, details)):
        color = ORANGE if i in (1, 2) else GREEN if i == 3 and progress >= .72 else INK
        p.text(41, y-9, f'0{i+1}', 14, GRAY)
        p.text(79, y-12, name, 20, bold=True)
        p.line([(311, y), (436, y)], FAINT)
        if i == 2:
            offset = round(64 * (1 - min(1, max(0, (progress-.2)/.34))))
            p.line([(455, y), (455+offset, y)], ORANGE, 2)
            p.line([(455+offset, y-8), (455+offset, y+8)], ORANGE, 3)
        else:
            p.line([(447, y), (463, y)], color, 2)
        p.text(550, y-12, detail, 21, color, mono=i == 2)
        if i == 3 and progress >= .72:
            p.line([(478, y), (482, y+4), (490, y-5)], GREEN, 2)

    if 0 < progress < 1:
        p.circle(455, 175 + round(progress * 215), 4, ORANGE if progress < .72 else GREEN)

    # A quiet return trace makes lasting knowledge part of the next change.
    route = [(912, 381), (912, 406), (332, 406), (332, 197), (436, 197)]
    for a, b in pairwise(route):
        p.line([a, b], FAINT)
    p.polygon([(436, 197), (429, 193), (429, 201)], FAINT)
    if progress >= .8:
        p.line([(912, 381), (912, 406), (778, 406)], GREEN, 2)
        p.circle(778, 406, 3, GREEN)
    p.line([(40, 438), (920, 438)], INK)
    p.text(41, 452, 'CHECKS PROVIDE EVIDENCE, NOT A GUARANTEE.', 14, GRAY)
    p.text(727, 452, 'READ / CHANGE / REMEMBER', 14, GRAY)
    return p


def main():
    # 64 palette frames use <29 MiB, with a 3-second finished-state hold.
    count = 64
    frames = []
    finished = render(1)
    palette = finished.image.quantize(colors=32)
    for i in range(count):
        # The opening and closing frame match; no flash or blank loop seam.
        progress = 1 if i < 3 or i >= 61 else (i-3)/57
        plate = render(progress)
        frames.append(plate.image.quantize(palette=palette, dither=Image.Dither.NONE))
    durations = [80] * count
    durations[-1] = 3000
    assert 50 <= count <= 72 and W <= 1000 and H <= 500
    assert count * W * H < 100 * 1024 * 1024
    assert sum(durations) == 8040 and frames[0].tobytes() == frames[-1].tobytes()
    finished.image.save(OUT / 'intent-poster.png')
    (OUT / 'intent-still.svg').write_text('\n'.join(finished.svg) + '\n</svg>\n')
    target = OUT / 'intent-loop.gif'
    frames[0].save(target, save_all=True, append_images=frames[1:], duration=durations,
                   loop=2, optimize=True, disposal=1)
    with Image.open(target) as gif:
        assert gif.size == (W, H) and gif.info['loop'] == 2
        assert 50 <= gif.n_frames <= 72
        actual_duration = 0
        observed = set()
        for i in range(gif.n_frames):
            gif.seek(i)
            actual_duration += gif.info['duration']
            observed.add(sha256(gif.convert('RGB').tobytes()).digest())
        assert len(observed) > 2 and actual_duration == sum(durations)
        gif.seek(0)
        first = gif.convert('RGB').tobytes()
        gif.seek(gif.n_frames-1)
        assert first == gif.convert('RGB').tobytes()
        assert target.stat().st_size < 700 * 1024
        print(f'{W}x{H}; {count} source frames, {gif.n_frames} encoded frames; '
              f'{actual_duration} ms; 3 plays, final frame held; {target.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
