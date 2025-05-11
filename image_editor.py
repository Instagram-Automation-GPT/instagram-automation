import os
from PIL import Image, ImageDraw
from Editors import center
from Editors import linear



def find_best_font_size(image_height, min_font_size=1, max_font_size=100):
    # Desired font height
    font_height = image_height // 14

    # Find the font size nearest to the desired font height
    best_font_size = min_font_size
    best_difference = abs(font_height - min_font_size)

    for font_size in range(min_font_size + 1, max_font_size + 1):
        difference = abs(font_height - font_size)
        if difference < best_difference:
            best_difference = difference
            best_font_size = font_size

    return best_font_size


def add_text_to_image(image_path, text, font_path, mode,current_time):
    formatted_time = current_time.strftime("%Y-%m-%d %H%M%S")
    output_path = image_path
    image = Image.open(image_path)
    font_size = find_best_font_size(image.height)
    if mode == "gradient":
        gradient_down = Image.new('L', (image.width, image.height), 0)
        gradient_up = Image.new('L', (image.width, image.height), 0)

        draw_down = ImageDraw.Draw(gradient_down)
        draw_up = ImageDraw.Draw(gradient_up)

        # Define the start and end black intensity for both gradients
        start_black_down = 128  # Start of black in the downward gradient
        start_black_up = 0  # Start of black in the upward gradient

        # Add downward gradient (from bottom to top)
        for y in range(image.height - 1, -1, -1):  # Loop from the bottom to the top
            blackness_down = int(255 * (image.height - y) / image.height)
            blackness_down = max(0, min(255, blackness_down))
            draw_down.line([(0, y), (image.width, y)], fill=blackness_down)

        # Add upward gradient (from top to bottom)
        for y in range(image.height):
            blackness_up = int(255 * (y + 1) / image.height)  # Adjusting y to avoid division by zero
            blackness_up = max(0, min(255, blackness_up))
            draw_up.line([(0, y), (image.width, y)], fill=blackness_up)

        linear_start_x = image.width / 20
        down_start_y = (image.height - font_size) / 6
        up_start_y = (image.height - font_size) / 20

        center_down_composite = Image.composite(image, Image.new('RGB', image.size, (0, 0, 0)), gradient_down)
        center_up_composite = Image.composite(image, Image.new('RGB', image.size, (0, 0, 0)), gradient_up)
        linear_down_composite = Image.composite(image, Image.new('RGB', image.size, (0, 0, 0)), gradient_down)
        linear_up_composite = Image.composite(image, Image.new('RGB', image.size, (0, 0, 0)), gradient_up)

        file_name, _ = os.path.splitext(os.path.basename(output_path))
        current_directory = os.getcwd()
        output_path = current_directory + "/outputs/" + file_name + f" {formatted_time}" + "/gradient"
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output_path = output_path + "\\" + file_name + _
        center_down_path = center.center(center_down_composite, text, font_path, font_size, image.width, image.height,
                                         down_start_y, output_path, "down")
        center_up_path = center.center(center_up_composite, text, font_path, font_size, image.width, image.height,
                                       up_start_y, output_path, "up")

        linear_down_path = linear.linear(linear_down_composite, text, font_path, font_size, image.width, image.height,
                                         linear_start_x,
                                         down_start_y, output_path, "down")
        linear_up_path = linear.linear(linear_up_composite, text, font_path, font_size, image.width, image.height,
                                       linear_start_x,
                                       up_start_y, output_path, "up")

        outputs = [center_down_path, center_up_path, linear_down_path, linear_up_path]

        return outputs
