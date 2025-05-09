import hashlib
import logging
import os.path

from PIL import Image, ImageDraw, ImageFont

from emulator.wall import DuplicateWall
from mortal.mortal_helpers import TILES


def get_wall_hash(wall: DuplicateWall) -> str:
    h = hashlib.md5()
    for tile in wall.shuffled_tiles:
        h.update(tile.encode())
    return h.hexdigest()


def get_file_path(pictures_dir: str, wall: DuplicateWall) -> str:
    filename = "wall_" + get_wall_hash(wall=wall)
    filename += "_" + wall.shuffled_tiles[0] + wall.shuffled_tiles[1]
    filename += "_" + wall.shuffled_tiles[-2] + wall.shuffled_tiles[-1]
    filename += ".png"
    return os.path.join(pictures_dir, filename)


def create_tile_image(tile: str, angle: int = 0) -> Image.Image:
    img_frame = Image.open("tiles_png/200/frame.png")
    img_tile = Image.open(f"tiles_png/200/{tile}.png")
    result = Image.alpha_composite(img_tile, img_frame)
    if angle != 0:
        result = result.rotate(angle, expand=True)
    return result


def create_text_image(text: str, width: int, height: int, font_size: int, angle: int = 0):
    result = Image.new("RGB", (width, height), "white")

    # uncomment for debug
    # ImageDraw.ImageDraw(result).rounded_rectangle(xy=(0, 0, width - 1, height - 1), radius=10, fill="black")
    # ImageDraw.ImageDraw(result).rounded_rectangle(xy=(4, 4, width - 5, height - 5), radius=10, fill="white")

    font = ImageFont.load_default(size=float(font_size))
    bbox = ImageDraw.ImageDraw(result).textbbox(xy=(0, 0), text=text, font=font, stroke_width=2)
    x = int(width / 2 - (bbox[2] - bbox[0]) / 2)
    y = int(height / 2 - (bbox[3] - bbox[1]) / 2)
    ImageDraw.ImageDraw(result).text(xy=(x, y), text=text, fill="black", font=font, stroke_width=2)

    if angle != 0:
        result = result.rotate(angle, expand=True)
    return result


def draw_duplicate_wall(wall: DuplicateWall):
    pictures_dir = "wall_pictures"
    if not os.path.exists(pictures_dir):
        os.mkdir(pictures_dir)
    file_path = get_file_path(pictures_dir=pictures_dir, wall=wall)
    logging.info("Will save picture to file %s", file_path)

    pic_width = 5500
    pic_height = 4000
    img = Image.new("RGB", (pic_width, pic_height), "white")

    tile_width = 200
    tile_height = int(tile_width * 4 / 3)
    blank_space = 5

    # East hand
    for i, tile in enumerate(sorted(wall.start_hands[0], key=lambda t: TILES.index(t))):
        tile_img = create_tile_image(tile=tile)
        x = int(pic_width / 2 - 6.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        y = pic_height - tile_height - blank_space
        img.paste(tile_img, (x, y))

    # South hand
    for i, tile in enumerate(sorted(wall.start_hands[1], key=lambda t: TILES.index(t))):
        tile_img = create_tile_image(tile=tile, angle=90)
        y = int(pic_height / 2 + 6.5 * (tile_width + blank_space) - (i + 1) * (tile_width + blank_space))
        x = pic_width - tile_height - blank_space
        img.paste(tile_img, (x, y))

    # West hand
    for i, tile in enumerate(sorted(wall.start_hands[2], key=lambda t: TILES.index(t))):
        tile_img = create_tile_image(tile=tile, angle=180)
        x = int(pic_width / 2 + 6.5 * (tile_width + blank_space) - (i + 1) * (tile_width + blank_space))
        y = blank_space
        img.paste(tile_img, (x, y))

    # North hand
    for i, tile in enumerate(sorted(wall.start_hands[3], key=lambda t: TILES.index(t))):
        tile_img = create_tile_image(tile=tile, angle=-90)
        y = int(pic_height / 2 - 6.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        x = blank_space
        img.paste(tile_img, (x, y))

    # East wall
    for i, tile in enumerate(wall.walls[0][16::-2]):
        tile_img = create_tile_image(tile=tile)
        caption_img = create_text_image(text="E0" + str(i), width=200, height=100, font_size=70)
        x = int(pic_width / 2 - 4.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        y = int(pic_height - 3.5 * tile_height - blank_space)
        img.paste(caption_img, (x, y - caption_img.height))
        img.paste(tile_img, (x, y))
    for i, tile in enumerate(wall.walls[0][17::-2]):
        tile_img = create_tile_image(tile=tile)
        caption_img = create_text_image(text="E1" + str(i), width=200, height=100, font_size=70)
        x = int(pic_width / 2 - 4.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        y = int(pic_height - 2.5 * tile_height)
        img.paste(caption_img, (x, y + tile_height - 30))
        img.paste(tile_img, (x, y))
    # "East" text
    text_img = create_text_image(text="East", width=500, height=150, font_size=100)
    x = int(pic_width / 2 - text_img.width / 2)
    y = int(pic_height - 4 * tile_height - blank_space - 1.2 * text_img.height)
    img.paste(text_img, (x, y))

    # South wall
    for i, tile in enumerate(wall.walls[1][16::-2]):
        tile_img = create_tile_image(tile=tile, angle=90)
        caption_img = create_text_image(text="S0" + str(i), width=200, height=100, font_size=70, angle=90)
        y = int(pic_height / 2 + 4.5 * (tile_width + blank_space) - (i + 1) * (tile_width + blank_space))
        x = int(pic_width - 3.5 * tile_height - blank_space)
        img.paste(caption_img, (x - caption_img.width, y))
        img.paste(tile_img, (x, y))
    for i, tile in enumerate(wall.walls[1][17::-2]):
        tile_img = create_tile_image(tile=tile, angle=90)
        caption_img = create_text_image(text="S1" + str(i), width=200, height=100, font_size=70, angle=90)
        y = int(pic_height / 2 + 4.5 * (tile_width + blank_space) - (i + 1) * (tile_width + blank_space))
        x = int(pic_width - 2.5 * tile_height)
        img.paste(caption_img, (x + tile_height - 30, y))
        img.paste(tile_img, (x, y))
    # "South" text
    text_img = create_text_image(text="South", width=500, height=150, font_size=100, angle=90)
    x = int(pic_width - 4 * tile_height - blank_space - 1.2 * text_img.width)
    y = int(pic_height / 2 - text_img.height / 2)
    img.paste(text_img, (x, y))

    # West wall
    for i, tile in enumerate(wall.walls[2][::2]):
        tile_img = create_tile_image(tile=tile, angle=180)
        caption_img = create_text_image(text="W0" + str(8 - i), width=200, height=100, font_size=70, angle=180)
        x = int(pic_width / 2 - 4.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        y = int(2.5 * tile_height + blank_space)
        img.paste(caption_img, (x, y + tile_height))
        img.paste(tile_img, (x, y))
    for i, tile in enumerate(wall.walls[2][1::2]):
        tile_img = create_tile_image(tile=tile, angle=180)
        caption_img = create_text_image(text="W1" + str(8 - i), width=200, height=100, font_size=70, angle=180)
        x = int(pic_width / 2 - 4.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        y = int(1.5 * tile_height)
        img.paste(caption_img, (x, y - caption_img.height + 30))
        img.paste(tile_img, (x, y))
    # "West" text
    text_img = create_text_image(text="West", width=500, height=150, font_size=100, angle=180)
    x = int(pic_width / 2 - text_img.width / 2)
    y = int(4 * tile_height + blank_space + 0.2 * text_img.height)
    img.paste(text_img, (x, y))

    # North wall
    for i, tile in enumerate(wall.walls[3][16::-2]):
        tile_img = create_tile_image(tile=tile, angle=-90)
        caption_img = create_text_image(text="N0" + str(i), width=200, height=100, font_size=70, angle=-90)
        y = int(pic_height / 2 - 4.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        x = int(2.5 * tile_height) + blank_space
        img.paste(caption_img, (x + tile_height, y))
        img.paste(tile_img, (x, y))
    for i, tile in enumerate(wall.walls[3][17::-2]):
        tile_img = create_tile_image(tile=tile, angle=-90)
        caption_img = create_text_image(text="N1" + str(i), width=200, height=100, font_size=70, angle=-90)
        y = int(pic_height / 2 - 4.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        x = int(1.5 * tile_height)
        img.paste(caption_img, (x - caption_img.width + 30, y))
        img.paste(tile_img, (x, y))
    # "North" text
    text_img = create_text_image(text="North", width=500, height=150, font_size=100, angle=-90)
    x = int(4 * tile_height + blank_space + 0.2 * text_img.width)
    y = int(pic_height / 2 - text_img.height / 2)
    img.paste(text_img, (x, y))

    # Dead wall
    for i, tile in enumerate(wall.dead_wall[-3::-2]):
        tile_img = create_tile_image(tile=tile)
        y = int(pic_height / 2)
        x = int(pic_width / 2 - 1.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        img.paste(tile_img, (x, y))
    for i, tile in enumerate(wall.dead_wall[11:9:-1] + wall.dead_wall[-4::-2]):
        tile_img = create_tile_image(tile=tile)
        y = int(pic_height / 2 + (tile_height + blank_space))
        x = int(pic_width / 2 - 3.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        img.paste(tile_img, (x, y))
    # "Dead wall" text
    text_img = create_text_image(text="Dead wall", width=500, height=150, font_size=100)
    x = int(pic_width / 2 - text_img.width / 2)
    y = int(pic_height / 2 - 1.2 * text_img.height)
    img.paste(text_img, (x, y))

    # Wall hash
    text_img = create_text_image(text="Hash: " + get_wall_hash(wall=wall), width=1700, height=150, font_size=80)
    x = int(pic_width / 2 - text_img.width / 2)
    y = int(pic_height / 2 - 3.2 * text_img.height)
    img.paste(text_img, (x, y))

    if os.path.exists(file_path):
        logging.info("File %s already exists!", file_path)
    else:
        img.save(file_path)
        logging.info("Duplicate wall picture saved to file %s", file_path)
