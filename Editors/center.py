import os
from PIL import Image, ImageDraw, ImageFont, ImageOps


def center(center_composite, text, font_path, font_size, width, height, start_y, output_path, mode):
    center_draw = ImageDraw.Draw(center_composite)
    # Load the font
    font = ImageFont.truetype(font_path, font_size)
    max_width = width
    # Split text based on ==
    center_line_segments = text.replace("\n", "").split("\r")
    # dots_count = center_line_segments.count(":")
    for line in center_line_segments:
        line_width = center_draw.textlength(line, font=font)
        while line_width > max_width / 0.75:
            font = ImageFont.truetype(font_path, font_size - 1)
            line_width = center_draw.textlength(line, font=font)

    left, top, right, bottom = font.getbbox("A")
    font_height = (bottom - top) * 1.5
    real_font_height =  bottom - top
    sub_height = 0
    if mode == "down":

        for i in range(0, len(center_line_segments)):
            sub_height += font_height
        start_y = height - sub_height
    # return start_y

    for line in center_line_segments:
        center_segments = line.split(" ")
        start_x = (max_width - center_draw.textlength(line.replace("$", ""), font=font)) / 2
        if len(center_segments) > 1:
            gap = " "
        else:
            gap = ""
        for segment in center_segments:
            if segment:  # Check if segment is not empty
                if start_x is None:
                    start_x = (max_width - center_draw.textlength(segment.replace("$", ""), font=font)) / 2
                if segment.startswith("$"):  # Red text
                    segment_width = center_draw.textlength(segment.replace("$", "") + gap, font=font)
                    center_draw.text((start_x, start_y), segment.replace("$", "") + gap, font=font, fill=(255, 0, 0))
		    # for bold font
                    # ,stroke_width=2, stroke_fill="red"
                else:  # Black text
                    segment_width = center_draw.textlength(segment + gap, font=font)
                    center_draw.text((start_x, start_y), segment + gap, font=font, fill=(255, 255, 255))
            start_x += segment_width
        start_y += font_height

    file_name, _ = os.path.basename(output_path).split(".")

    new_file_name = file_name + f"_center_{mode}" + "." + _
    output_path = output_path.replace(os.path.basename(output_path), new_file_name).replace("\\","/")
    center_composite.save(output_path)
    print(output_path)
    return output_path
