#!/usr/bin/env python3

import argparse
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageColor


# ---------- parsing helpers ----------

def wrap_text(draw, text, font, max_width, spacing=4):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = word if not current else current + " " + word

        bbox = draw.multiline_textbbox(
            (0, 0),
            test,
            font=font,
            spacing=spacing
        )
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return "\n".join(lines)

def parse_padding(padding_str, image_height):
    padding_str = padding_str.strip()

    percent_match = re.fullmatch(r"%?(\d+)%?", padding_str)
    if "%" in padding_str and percent_match:
        percent = int(percent_match.group(1))
        return int(image_height * (percent / 100))

    if padding_str.isdigit():
        return int(padding_str)

    raise ValueError(f"Invalid padding value: {padding_str}")


def parse_pixels_or_percent(value, base):
    value = value.strip()
    percent_match = re.fullmatch(r"%?(\d+)%?", value)
    if "%" in value and percent_match:
        return int(base * (int(percent_match.group(1)) / 100))
    if value.isdigit():
        return int(value)
    raise ValueError(f"Invalid value: {value}")


def parse_color(color_str):
    color_str = color_str.strip()

    # RGB: 255,255,255
    if re.fullmatch(r"\d{1,3},\d{1,3},\d{1,3}", color_str):
        r, g, b = map(int, color_str.split(","))
        for v in (r, g, b):
            if not 0 <= v <= 255:
                raise ValueError("RGB values must be between 0 and 255")
        return (r, g, b)

    # Hex without '#'
    if re.fullmatch(r"[0-9a-fA-F]{6}|[0-9a-fA-F]{3}", color_str):
        color_str = "#" + color_str

    try:
        return ImageColor.getrgb(color_str)
    except ValueError:
        raise ValueError(f"Invalid color value: {color_str}")


def load_font(font_path, font_size):
    if not font_path.endswith(".ttf"):
        font_path += ".ttf"
    try:
        if font_path:
            return ImageFont.truetype(font_path, font_size)
        return ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        return ImageFont.load_default()


def wrap_for_multiline(draw, text, font, max_width):
    # Normalize escaped newlines
    text = text.replace("\\n", "\n")

    approx_chars_per_line = max_width // 5

    wrapped_blocks = []
    for paragraph in text.split("\n"):
        if paragraph.strip() == "":
            wrapped_blocks.append("")
        else:
            wrapped_blocks.append(
                textwrap.fill(paragraph, width=approx_chars_per_line)
            )

    return "\n".join(wrapped_blocks)


# ---------- main image logic ----------

def process_image(
    input_image,
    output_image,
    comment,
    padding,
    bg_color,
    text_color,
    font_path,
    font_size,
    align,
    valign,
    wrap_width,
):
    img = Image.open(input_image).convert("RGB")
    width, height = img.size

    bottom_padding = parse_padding(padding, height)
    bg_rgb = parse_color(bg_color)
    text_rgb = parse_color(text_color)

    new_img = Image.new(
        "RGB", (width, height + bottom_padding), bg_rgb
    )
    new_img.paste(img, (0, 0))

    draw = ImageDraw.Draw(new_img)
    font = load_font(font_path, font_size)

    max_text_width = parse_pixels_or_percent(wrap_width, width)
    wrapped_text = wrap_for_multiline(
        draw, comment, font, max_text_width
    )

    bbox = draw.multiline_textbbox(
        (0, 0),
        wrapped_text,
        font=font,
        spacing=4,
        align=align,
    )

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Vertical alignment
    if valign == "top":
        y = height + 10
    elif valign == "bottom":
        y = height + bottom_padding - text_height - 10
    else:  # middle
        y = height + (bottom_padding - text_height) // 2

    # Horizontal alignment
    if align == "left":
        x = 20
    elif align == "right":
        x = width - text_width - 20
    else:
        x = (width - text_width) // 2

    draw.multiline_text(
        (x, y),
        wrapped_text,
        fill=text_rgb,
        font=font,
        spacing=4,
        align=align,
    )

    new_img.save(output_image)
    print(f"[+] Saved output image to: {output_image}")


# ---------- CLI ----------

def main():
    parser = argparse.ArgumentParser(
        description="Add a comment area to the bottom of an image"
    )

    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-c", "--comment", required=True)

    parser.add_argument(
        "-p", "--padding",
        default="200",
        help="Bottom padding (pixels or %%)"
    )

    parser.add_argument(
        "-b", "--bg-color",
        default="black",
        help="Background color of padding"
    )

    parser.add_argument(
        "-t", "--text-color",
        default="white",
        help="Text color"
    )

    parser.add_argument(
        "-f", "--font",
        default="arial",
        help="Font name or path"
    )

    parser.add_argument(
        "-s", "--font-size",
        type=int,
        default=16,
        help="Font size"
    )

    parser.add_argument(
        "-a", "--align",
        choices=["left", "center", "right"],
        default="left",
        help="Horizontal alignment"
    )

    parser.add_argument(
        "--valign",
        choices=["top", "middle", "bottom"],
        default="top",
        help="Vertical alignment inside padding"
    )

    parser.add_argument(
        "--wrap-width",
        default="90%",
        help="Wrap width (pixels or %% of image width)"
    )

    args = parser.parse_args()

    try:
        process_image(
            args.input,
            args.output,
            args.comment,
            args.padding,
            args.bg_color,
            args.text_color,
            args.font,
            args.font_size,
            args.align,
            args.valign,
            args.wrap_width,
        )
    except ValueError as e:
        parser.error(str(e))


if __name__ == "__main__":
    main()
