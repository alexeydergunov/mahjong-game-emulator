import hashlib
import logging
import os.path

from PIL import Image, ImageDraw, ImageFont

from emulator.wall import DuplicateWall
from mortal.mortal_helpers import TILES


def get_file_path(pictures_dir: str, wall: DuplicateWall) -> str:
    h = hashlib.md5()
    for tile in wall.shuffled_tiles:
        h.update(tile.encode())
    filename = "wall_" + h.hexdigest()
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


def create_tile_back_with_text(color: str, text: str, angle: int = 0) -> Image.Image:
    result = Image.new("RGB", (200, 266), "white")
    ImageDraw.ImageDraw(result).rounded_rectangle(xy=(0, 0, 199, 265), radius=10, fill="black")
    ImageDraw.ImageDraw(result).rounded_rectangle(xy=(4, 4, 195, 261), radius=10, fill=color)

    font = ImageFont.load_default(size=float(85))
    bbox = ImageDraw.ImageDraw(result).textbbox(xy=(0, 0), text=text, font=font, stroke_width=2)
    x = int(100 - (bbox[2] - bbox[0]) / 2)
    y = int(133 - (bbox[3] - bbox[1]) / 2)
    ImageDraw.ImageDraw(result).text(xy=(x, y), text=text, fill="black", font=font, stroke_width=2)

    if angle != 0:
        result = result.rotate(angle, expand=True)
    return result


def draw_duplicate_wall(wall: DuplicateWall):
    pictures_dir = "wall_pictures"
    if not os.path.exists(pictures_dir):
        os.mkdir(pictures_dir)
    file_path = os.path.join(pictures_dir, "duplicate_marks.png")
    logging.info("Will save picture to file %s", file_path)

    pic_width = 4000
    pic_height = 4000
    img = Image.new("RGB", (pic_width, pic_height), "white")

    tile_width = 200
    tile_height = int(tile_width * 4 / 3)
    blank_space = 5

    # East hand
    for i, tile in enumerate(sorted(wall.start_hands[0], key=lambda t: TILES.index(t))):
        tile_img = create_tile_back_with_text(color="red", text="E")
        x = int(pic_width / 2 - 6.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        y = pic_height - tile_height - blank_space
        img.paste(tile_img, (x, y))

    # South hand
    for i, tile in enumerate(sorted(wall.start_hands[1], key=lambda t: TILES.index(t))):
        tile_img = create_tile_back_with_text(color="gold", text="S", angle=90)
        y = int(pic_height / 2 + 6.5 * (tile_width + blank_space) - (i + 1) * (tile_width + blank_space))
        x = pic_width - tile_height - blank_space
        img.paste(tile_img, (x, y))

    # West hand
    for i, tile in enumerate(sorted(wall.start_hands[2], key=lambda t: TILES.index(t))):
        tile_img = create_tile_back_with_text(color="limegreen", text="W", angle=180)
        x = int(pic_width / 2 + 6.5 * (tile_width + blank_space) - (i + 1) * (tile_width + blank_space))
        y = blank_space
        img.paste(tile_img, (x, y))

    # North hand
    for i, tile in enumerate(sorted(wall.start_hands[3], key=lambda t: TILES.index(t))):
        tile_img = create_tile_back_with_text(color="skyblue", text="N", angle=-90)
        y = int(pic_height / 2 - 6.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        x = blank_space
        img.paste(tile_img, (x, y))

    # East wall
    for i, tile in enumerate(wall.walls[0][16::-2]):
        tile_img = create_tile_back_with_text(color="red", text="E0" + str(i))
        x = int(pic_width / 2 - 4.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        y = int(pic_height - 3.5 * tile_height - blank_space)
        img.paste(tile_img, (x, y))
    for i, tile in enumerate(wall.walls[0][17::-2]):
        tile_img = create_tile_back_with_text(color="red", text="E1" + str(i))
        x = int(pic_width / 2 - 4.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        y = int(pic_height - 2.5 * tile_height)
        img.paste(tile_img, (x, y))

    # South wall
    for i, tile in enumerate(wall.walls[1][16::-2]):
        tile_img = create_tile_back_with_text(color="gold", text="S0" + str(i), angle=90)
        y = int(pic_height / 2 + 4.5 * (tile_width + blank_space) - (i + 1) * (tile_width + blank_space))
        x = int(pic_width - 3.5 * tile_height - blank_space)
        img.paste(tile_img, (x, y))
    for i, tile in enumerate(wall.walls[1][17::-2]):
        tile_img = create_tile_back_with_text(color="gold", text="S1" + str(i), angle=90)
        y = int(pic_height / 2 + 4.5 * (tile_width + blank_space) - (i + 1) * (tile_width + blank_space))
        x = int(pic_width - 2.5 * tile_height)
        img.paste(tile_img, (x, y))

    # West wall
    for i, tile in enumerate(wall.walls[2][::2]):
        tile_img = create_tile_back_with_text(color="limegreen", text="W0" + str(8 - i), angle=180)
        x = int(pic_width / 2 - 4.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        y = int(2.5 * tile_height + blank_space)
        img.paste(tile_img, (x, y))
    for i, tile in enumerate(wall.walls[2][1::2]):
        tile_img = create_tile_back_with_text(color="limegreen", text="W1" + str(8 - i), angle=180)
        x = int(pic_width / 2 - 4.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        y = int(1.5 * tile_height)
        img.paste(tile_img, (x, y))

    # North wall
    for i, tile in enumerate(wall.walls[3][16::-2]):
        tile_img = create_tile_back_with_text(color="skyblue", text="N0" + str(i), angle=-90)
        y = int(pic_height / 2 - 4.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        x = int(2.5 * tile_height) + blank_space
        img.paste(tile_img, (x, y))
    for i, tile in enumerate(wall.walls[3][17::-2]):
        tile_img = create_tile_back_with_text(color="skyblue", text="N1" + str(i), angle=-90)
        y = int(pic_height / 2 - 4.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        x = int(1.5 * tile_height)
        img.paste(tile_img, (x, y))

    # Dead wall
    for i, tile in enumerate(wall.dead_wall[-3::-2]):
        tile_img = create_tile_back_with_text(color="darkgrey" if i > 0 else "lightgrey", text="D0" + str(i + 2))
        y = int(pic_height / 2 - (tile_height + blank_space))
        x = int(pic_width / 2 - 1.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        img.paste(tile_img, (x, y))
    for i, tile in enumerate(wall.dead_wall[11:9:-1] + wall.dead_wall[-4::-2]):
        tile_img = create_tile_back_with_text(color="darkgrey", text="D1" + str(i))
        y = int(pic_height / 2)
        x = int(pic_width / 2 - 3.5 * (tile_width + blank_space) + i * (tile_width + blank_space))
        img.paste(tile_img, (x, y))

    if os.path.exists(file_path):
        logging.info("File %s already exists!", file_path)
    else:
        img.save(file_path)
        logging.info("Duplicate wall picture saved to file %s", file_path)
