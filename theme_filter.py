import numpy as np
from PIL import Image, ImageOps
import json
import os
import argparse

THEMES = "themes.json"


def load_themes(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def find_nearest_color(pixel, theme):
    distances = np.sqrt(np.sum((theme - pixel) ** 2, axis=1))
    return theme[np.argmin(distances)]


def pad_to_landscape(img_array):
    height, width, _ = img_array.shape

    # Check if image is already in landscape format
    if width >= height * (16 / 9):
        return img_array  # No padding needed

    # Calculate required padding to make the image landscape
    padding_needed = int((height * (16 / 9) - width) // 2)

    # Determine the border color (you can use the theme or average color)
    first_column_pixels = img_array[:, 0, :]  # Extract the first column of pixels
    border_color = np.median(first_column_pixels, axis=0).astype(np.uint8)

    # Convert to a PIL Image for easy padding
    img = Image.fromarray(img_array.astype('uint8'))

    # Apply padding on left and right
    padded_img = ImageOps.expand(img, border=(padding_needed, 0, padding_needed, 0), fill=tuple(border_color))

    # Convert back to NumPy array
    return np.array(padded_img)


def apply_theme(image_path, theme, output_path, negative=False, landscape=False):
    if os.path.isdir(image_path):
        for file in os.listdir(image_path):
            apply_theme(os.path.join(image_path, file), theme, os.path.join(output_path, file), negative, landscape)
        return
    img = Image.open(image_path)

    # Convert image to RGB if it's in RGBA mode
    if img.mode == 'RGBA':
        print("Image has an alpha channel. Converting to RGB and discarding opacity.")
        img = img.convert('RGB')
    img_array = np.array(img)
    if negative:
        img_array = 255 - img_array
    themes = load_themes(THEMES)
    theme = np.array(themes[theme])

    # Pad the image to make it landscape
    if landscape:
        img_array = pad_to_landscape(img_array)

    # Apply the theme
    shape = img_array.shape
    flat_img = img_array.reshape(-1, 3)

    # Apply the nearest color theme (using a list comprehension)
    vectorized_find_nearest = np.vectorize(find_nearest_color, signature='(n),(m,n)->(n)')
    result = vectorized_find_nearest(flat_img, theme)

    # Reshape the result back to the padded image shape
    result_img = result.reshape(shape)

    # Save the result
    Image.fromarray(result_img.astype('uint8')).save(output_path)
    print(f"Themed image saved as {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Apply a color theme to an image.")
    parser.add_argument("image_path", help="Path to the input image")
    parser.add_argument("theme_name", help="Name of the theme to apply")
    parser.add_argument("output_path", help="Path for the output image")
    parser.add_argument("--negative", action="store_true", help="Apply the theme to the negative of the image")
    parser.add_argument("--landscape", action="store_true",
                        help="Pad the image left and right untill it reaches landscape ratio")

    args = parser.parse_args()

    apply_theme(args.image_path, args.theme_name, args.output_path, negative=args.negative, landscape=args.landscape)


if __name__ == "__main__":
    main()
