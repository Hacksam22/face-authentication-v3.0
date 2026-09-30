"""Generate the ANMS Attendance logo PNG and Windows ICO with Pillow."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = ROOT / "assets"
SCALE = 3
SIZE = 768


def box(coords):
    return tuple(round(value * SCALE) for value in coords)


def curve(start, control_a, control_b, end, steps=28):
    result = []
    for index in range(steps + 1):
        t = index / steps
        inverse = 1 - t
        x = inverse**3 * start[0] + 3 * inverse**2 * t * control_a[0] + 3 * inverse * t**2 * control_b[0] + t**3 * end[0]
        y = inverse**3 * start[1] + 3 * inverse**2 * t * control_a[1] + 3 * inverse * t**2 * control_b[1] + t**3 * end[1]
        result.append((round(x * SCALE), round(y * SCALE)))
    return result


def draw_logo():
    image = Image.new("RGBA", (SIZE * SCALE, SIZE * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.ellipse(box((42, 42, 726, 726)), fill="#082C50")
    draw.ellipse(box((55, 55, 713, 713)), fill="#35B9B0")
    draw.ellipse(box((68, 68, 700, 700)), fill="#F9FCFC")
    draw.ellipse(box((82, 82, 686, 686)), fill="#073456")
    draw.ellipse(box((96, 96, 672, 672)), fill="#35B9B0")
    draw.ellipse(box((108, 108, 660, 660)), fill="#0A5573")

    shield = [(384, 74), (431, 95), (428, 145), (409, 171), (384, 190), (359, 171), (340, 145), (337, 95)]
    draw.polygon([(x * SCALE, y * SCALE) for x, y in shield], fill="#51D2C8", outline="#0A3457", width=5 * SCALE)
    draw.line([(367 * SCALE, 108 * SCALE), (367 * SCALE, 145 * SCALE), (384 * SCALE, 161 * SCALE), (401 * SCALE, 145 * SCALE), (401 * SCALE, 108 * SCALE), (384 * SCALE, 99 * SCALE), (367 * SCALE, 108 * SCALE)], fill="#0B4770", width=7 * SCALE, joint="curve")

    circuits = [
        [(147, 257), (216, 257), (244, 229), (290, 229)],
        [(137, 296), (201, 296), (225, 275), (281, 275)],
        [(153, 339), (220, 339), (245, 319), (280, 319)],
        [(177, 389), (225, 389), (253, 369), (284, 369)],
        [(183, 431), (230, 431), (253, 414), (294, 414)],
    ]
    for points in circuits:
        draw.line([(x * SCALE, y * SCALE) for x, y in points], fill="#48D6D0", width=5 * SCALE, joint="curve")
        for x, y in (points[0], points[-1]):
            draw.ellipse(box((x - 7, y - 7, x + 7, y + 7)), fill="#72F2E6")

    profile = []
    profile += curve((291, 212), (333, 171), (408, 172), (448, 211))[:-1]
    profile += curve((448, 211), (468, 235), (466, 272), (465, 301))[:-1]
    profile += curve((465, 301), (463, 322), (478, 335), (495, 351))[:-1]
    profile += curve((495, 351), (501, 359), (488, 366), (478, 371))[:-1]
    profile += curve((478, 371), (489, 379), (489, 386), (475, 392))[:-1]
    profile += curve((475, 392), (489, 402), (482, 412), (463, 416))[:-1]
    profile += curve((463, 416), (461, 442), (446, 456), (421, 467))[:-1]
    profile += curve((421, 467), (391, 481), (350, 475), (321, 457))[:-1]
    profile += curve((321, 457), (278, 431), (266, 381), (268, 320))[:-1]
    profile += curve((268, 320), (269, 270), (273, 234), (291, 212))
    draw.polygon(profile, fill="#8DE0D7", outline="#E8FFFF", width=5 * SCALE)

    hair = [(278, 281), (261, 246), (271, 210), (304, 183), (352, 169), (405, 177), (439, 204), (449, 236), (424, 222), (400, 211), (374, 231), (344, 248), (314, 250)]
    draw.polygon([(x * SCALE, y * SCALE) for x, y in hair], fill="#092C51")
    draw.line([(x * SCALE, y * SCALE) for x, y in [(281, 264), (318, 239), (354, 232), (388, 207), (420, 214)]], fill="#37B9BE", width=8 * SCALE, joint="curve")
    draw.line([(x * SCALE, y * SCALE) for x, y in [(277, 281), (313, 260), (349, 254), (385, 232)]], fill="#1C7EA0", width=6 * SCALE, joint="curve")

    draw.ellipse(box((277, 305, 326, 370)), fill="#4BABB7", outline="#0C5275", width=5 * SCALE)
    draw.arc(box((289, 319, 317, 357)), 255, 100, fill="#0B466B", width=5 * SCALE)
    draw.line([(393 * SCALE, 303 * SCALE), (419 * SCALE, 294 * SCALE), (443 * SCALE, 302 * SCALE)], fill="#0A3B60", width=9 * SCALE, joint="curve")
    draw.line([(397 * SCALE, 329 * SCALE), (421 * SCALE, 321 * SCALE), (443 * SCALE, 329 * SCALE), (423 * SCALE, 339 * SCALE)], fill="#F4FFFF", width=5 * SCALE, joint="curve")
    draw.ellipse(box((416, 323, 428, 335)), fill="#073456")
    draw.line([(457 * SCALE, 330 * SCALE), (470 * SCALE, 350 * SCALE), (485 * SCALE, 357 * SCALE)], fill="#2A99AC", width=5 * SCALE, joint="curve")
    draw.line([(460 * SCALE, 393 * SCALE), (447 * SCALE, 398 * SCALE), (431 * SCALE, 395 * SCALE)], fill="#0C4A6A", width=5 * SCALE, joint="curve")

    nodes = [(347, 291), (366, 325), (385, 359), (407, 390), (431, 420), (374, 405), (333, 371)]
    draw.line([(x * SCALE, y * SCALE) for x, y in nodes], fill="#D7FFFF", width=3 * SCALE, joint="curve")
    for x, y in nodes:
        draw.ellipse(box((x - 5, y - 5, x + 5, y + 5)), fill="#F5FFFF", outline="#44C8C2", width=2 * SCALE)

    draw.rounded_rectangle(box((86, 493, 682, 652)), radius=20 * SCALE, fill="#FFFFFF")
    fonts = Path("C:/Windows/Fonts")
    bold_path = fonts / "arialbd.ttf"
    regular_path = fonts / "arial.ttf"
    title_font = ImageFont.truetype(str(bold_path), 112 * SCALE) if bold_path.exists() else ImageFont.load_default()
    subtitle_path = regular_path if regular_path.exists() else bold_path
    subtitle_font = ImageFont.truetype(str(subtitle_path), 49 * SCALE) if subtitle_path.exists() else ImageFont.load_default()
    draw.text((384 * SCALE, 496 * SCALE), "ANMS", font=title_font, fill="#092D53", anchor="mt")
    draw.text((384 * SCALE, 602 * SCALE), "ATTENDANCE", font=subtitle_font, fill="#17688D", anchor="mt")
    draw.line([(274 * SCALE, 675 * SCALE), (365 * SCALE, 675 * SCALE), (384 * SCALE, 694 * SCALE), (403 * SCALE, 675 * SCALE), (494 * SCALE, 675 * SCALE)], fill="#49BDB5", width=6 * SCALE, joint="curve")
    return image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def main():
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    logo = draw_logo()
    logo.save(ASSET_DIR / "app_logo.png", optimize=True)
    logo.save(ASSET_DIR / "app_logo.ico", format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Generated {ASSET_DIR / 'app_logo.png'} and {ASSET_DIR / 'app_logo.ico'}")


if __name__ == "__main__":
    main()