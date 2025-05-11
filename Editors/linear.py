import os
from PIL import Image, ImageDraw, ImageFont, ImageOps


def linear(linear_composite, text, font_path, font_size, width, height, start_x, start_y, output_path, mode):
    linear_draw = ImageDraw.Draw(linear_composite)
    # Load the font
    font = ImageFont.truetype(font_path, font_size)

    # Split text based on ==
    linear_segments = text.replace("\n", "").replace("\r","\r ").split(" ")
    linear_line_segments = text.replace("\n", "").split("\r")
    max_width = width  # Assuming image_width is the maximum width of the image
    left, top, right, bottom = font.getbbox("A")
    font_height = (bottom - top) * 1.5
    # overline = True

    sub_height = 0
    if mode == "down":
        for i in range(0, len(linear_line_segments)):
            sub_height += font_height
        start_y = height - sub_height
    for line in linear_line_segments:
        linear_segments = line.split(" ")
        start_x = width / 20
        if len(linear_segments) > 1:
            gap = " "
        else:
            gap = ""
        for segment in linear_segments:
            if segment:  # Check if segment is not empty
                if segment.startswith("$"):  # Red text

                    segment_width = linear_draw.textlength(segment.replace("$", "") + gap, font=font)
                    linear_draw.text((start_x, start_y), segment.replace("$", "") + gap, font=font, fill=(255, 0, 0))
		    # for bold font
                    # ,stroke_width=2, stroke_fill="red"
                else:  # Black text
                    segment_width = linear_draw.textlength(segment + gap, font=font)
                    linear_draw.text((start_x, start_y), segment + gap, font=font, fill=(255, 255, 255))
            start_x += segment_width
        start_y += font_height

    file_name, _ = os.path.basename(output_path).split(".")
    new_file_name = file_name + f"_linear_{mode}" + "." + _
    output_path = output_path.replace(os.path.basename(output_path), new_file_name).replace("\\","/")
    linear_composite.save(output_path)
    return output_path

