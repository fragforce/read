import io

import qrcode
import qrcode.image.svg
from PIL import Image, ImageDraw, ImageFont


def generate_qr_png(url, box_size=10, border=4):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")


def generate_qr_svg(url):
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    factory = qrcode.image.svg.SvgPathImage
    return qr.make_image(image_factory=factory)


def _wrap_text(text, font, max_width, draw):
    words = text.split("/")
    if len(words) <= 1:
        words = text.split()
        joiner = " "
    else:
        joiner = "/"

    lines = []
    current = words[0]
    for word in words[1:]:
        test = current + joiner + word
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current = test
        else:
            lines.append(current + (joiner if joiner == "/" else ""))
            current = word
    lines.append(current)
    return lines


def generate_label_png(url, book_title, narrator_name, password=None):
    qr_img = generate_qr_png(url, box_size=8, border=2)
    qr_size = qr_img.pixel_size

    padding = 20
    text_x = qr_size + padding * 2
    label_width = 700
    text_area_width = label_width - text_x - padding

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
        font_small = font
        font_title = font

    temp_img = Image.new("RGB", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)

    text_lines = []
    text_lines.append((book_title, font_title))
    text_lines.append((f"Read by {narrator_name}", font))
    if password:
        text_lines.append((f"Password: {password}", font))
    text_lines.append(("", font))

    for wrapped in _wrap_text(url, font_small, text_area_width, temp_draw):
        text_lines.append((wrapped, font_small))

    text_lines.append(("", font))
    text_lines.append(("Fragforce Reads", font))

    line_height = 22
    label_height = max(qr_size + padding * 2, len(text_lines) * line_height + padding * 2)

    img = Image.new("RGB", (label_width, label_height), "white")
    img.paste(qr_img.get_image(), (padding, padding))

    draw = ImageDraw.Draw(img)
    y = padding
    for text, f in text_lines:
        draw.text((text_x, y), text, fill="black", font=f)
        y += line_height

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
