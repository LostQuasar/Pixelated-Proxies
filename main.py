import os
import random
from subprocess import Popen
from textwrap import wrap
import time
import requests
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from card_info import *
import toml

INCH = 900
WIDTH, HEIGHT = int(2.5 * INCH), int(3.5 * INCH)
BOTTOM_OFFSET = 120
MARGIN = INCH / 6
CENTER_GAP = INCH / 16
DOWN_COUNT = 0
ENHANCE_COUNT = 0
ASCII_COUNT = 0
GEN_COUNT = 0


def download_art_crop(face: CardFace):
    global DOWN_COUNT
    img = Image.open(requests.get(face.ART, stream=True).raw)
    img.save(f'art_crops/{face.PATH}.jpg')
    DOWN_COUNT += 1
    time.sleep(0.4)
    generate_ascii_art(face)


def generate_ascii_art(face: CardFace):
    global ASCII_COUNT
    width = 0

    if face.LAYOUT is Layout.SPLIT:
        width = int((INCH * 3.125) / (font_size + 2))
    else:
        width = int((INCH * 2.25) / (font_size + 2))
    
    Popen(
        f'image-to-ascii art_crops/{face.PATH}.jpg -w{width} -f {font_path} -b0 -o ascii/{face.PATH}.png',
        shell=True
    )
    ASCII_COUNT += 1
    time.sleep(0.4)


font_size = 0
font_path = ''
with open('config.toml', 'r') as conf:
    config = toml.loads(conf.read())
    font_path = config['font']
    with open(font_path, 'r') as font:
        for line in font:
            if line.startswith('SIZE'):
                font_size = int(line.split(' ')[1])

print(font_path, font_size)

with open('input.csv', 'r') as file:
    font_bold = ImageFont.truetype('Hack-Bold.ttf', 80)
    font_medium_bold = ImageFont.truetype('Hack-Bold.ttf', 70)
    font_medium = ImageFont.truetype('Hack-Regular.ttf', 70)
    font_ital = ImageFont.truetype('Hack-Italic.ttf', 70)
    font_small = ImageFont.truetype('Hack-Regular.ttf', 60)
    font_small_ital = ImageFont.truetype('Hack-Italic.ttf', 60)

    for line in file.readlines():
        line = line.strip().split(',')
        if line[0].startswith('plst'):
            code, num = line[1].split('-')
        else:
            code, num = line

        card: CardInfo = CardInfo(code, num)

        for face in card.FACES:
            if not os.path.exists(f"art_crops/{face.PATH}.jpg"):
                download_art_crop(face)
                generate_ascii_art(face)

            # elif not os.path.exists(f"ascii/{face.PATH}.png"):
            generate_ascii_art(face)

            card_img = Image.new('RGB', (WIDTH, HEIGHT), (0, 0, 0))

            with Image.open(f'ascii/{face.PATH}.png') as ascii_art:
                ascii_art = ImageEnhance.Contrast(ascii_art).enhance(1.2)
                ascii_art = ImageEnhance.Color(ascii_art).enhance(1.3)
                vert_offset = 0
                hor_offset = 0
                if face.LAYOUT is Layout.SPLIT:
                    ascii_art = ascii_art.rotate(90, expand=True)
                    vert_offset = 570 - 80
                    hor_offset = 225
                if face.FULL_ART:
                    vert_offset = 500
                if face.LAYOUT is Layout.FLIP:
                    vert_offset = 570 - BOTTOM_OFFSET
                ascii_art = ascii_art.resize(
                    (ascii_art.width * 2, ascii_art.height * 2),
                    resample=Image.Resampling.NEAREST
                )
                card_img.paste(
                    ascii_art,
                    (
                        int((WIDTH / 2) - (ascii_art.width / 2) - hor_offset),
                        int((HEIGHT / 2) - (ascii_art.height / 2) - 570 + vert_offset)
                    )
                )

            draw = ImageDraw.Draw(card_img)
            if face.LAYOUT is Layout.NORMAL or face.LAYOUT is Layout.TRANSFORM:
                draw.text((MARGIN, MARGIN), f'> {face.NAME[0]}', font=font_bold)
                text_len = draw.textlength(face.MANA_COST[0], font=font_bold)
                draw.text(
                    (WIDTH - MARGIN - text_len, MARGIN),
                    face.MANA_COST[0],
                    font=font_bold
                )
                if not face.FULL_ART:
                    draw.text(
                        (MARGIN, INCH * 1.95), face.TYPE_LINE[0], font=font_medium_bold
                    )
                    if face.ORACLE_TEXT:
                        draw.text(
                            (MARGIN + 80, INCH * 2.1),
                            face.ORACLE_TEXT[0],
                            font=font_medium
                        )

                if face.FLAVOR_TEXT:
                    draw.text(
                        (
                            MARGIN + 80,
                            INCH * 2.1
                            + (face.ORACLE_TEXT[0].count('\n') + 1.5)
                            * font_medium.size
                        ),
                        face.FLAVOR_TEXT[0],
                        font=font_ital
                    )
            elif face.LAYOUT is Layout.SPLIT:
                rot_image = Image.new('RGBA', (HEIGHT, WIDTH), (0, 0, 0, 0))
                rot_draw = ImageDraw.Draw(rot_image)
                rot_draw.text(
                    (MARGIN + 150, MARGIN), f'> {face.NAME[0]}', font=font_bold
                )
                rot_draw.text(
                    (CENTER_GAP + HEIGHT / 2, MARGIN),
                    f'> {face.NAME[1]}',
                    font=font_bold
                )
                text_len = draw.textlength(face.MANA_COST[0], font=font_bold)
                rot_draw.text(
                    (HEIGHT / 2 - CENTER_GAP - text_len, MARGIN),
                    face.MANA_COST[0],
                    font=font_bold
                )
                text_len = draw.textlength(face.MANA_COST[1], font=font_bold)
                rot_draw.text(
                    (HEIGHT - MARGIN - text_len, MARGIN),
                    face.MANA_COST[1],
                    font=font_bold
                )
                rot_draw.text(
                    (MARGIN + 150, INCH * 1.625),
                    face.TYPE_LINE[0],
                    font=font_medium_bold
                )
                rot_draw.text(
                    (CENTER_GAP + HEIGHT / 2, INCH * 1.625),
                    face.TYPE_LINE[1],
                    font=font_medium_bold
                )

                if face.ORACLE_TEXT:
                    rot_draw.text(
                        (MARGIN + 150, INCH * 1.75),
                        face.ORACLE_TEXT[0],
                        font=font_medium
                    )
                    rot_draw.text(
                        (HEIGHT / 2 + CENTER_GAP, INCH * 1.75),
                        face.ORACLE_TEXT[1],
                        font=font_medium
                    )
                rot_image = rot_image.rotate(90, expand=True)
                card_img.paste(rot_image, mask=rot_image)
            elif face.LAYOUT is Layout.ADVENTURE:
                draw.text((MARGIN, MARGIN), f'> {face.NAME[0]}', font=font_bold)
                text_len = draw.textlength(face.MANA_COST[0], font=font_bold)
                draw.text(
                    (WIDTH - MARGIN - text_len, MARGIN),
                    face.MANA_COST[0],
                    font=font_bold
                )

                draw.text(
                    (MARGIN, INCH * 1.95), face.TYPE_LINE[0], font=font_medium_bold
                )

                if face.ORACLE_TEXT:
                    draw.text(
                        (WIDTH / 2 + CENTER_GAP, INCH * 2.2),
                        face.ORACLE_TEXT[0],
                        font=font_medium
                    )
                    draw.text(
                        (MARGIN, INCH * 2.4), face.ORACLE_TEXT[1], font=font_medium
                    )
                if face.FLAVOR_TEXT:
                    draw.text(
                        (
                            WIDTH / 2 + CENTER_GAP,
                            INCH * 2.2
                            + (face.ORACLE_TEXT[0].count('\n') + 1.5)
                            * font_medium.size
                        ),
                        face.FLAVOR_TEXT[0],
                        font=font_ital
                    )

                draw.text(
                    (MARGIN, INCH * 2.125), f'{face.NAME[1]}', font=font_medium_bold
                )
                text_len = draw.textlength(face.MANA_COST[1], font=font_medium_bold)
                draw.text(
                    (WIDTH / 2 - CENTER_GAP - text_len, INCH * 2.125),
                    face.MANA_COST[1],
                    font=font_medium_bold
                )

                draw.text(
                    (MARGIN, INCH * 2.25), face.TYPE_LINE[1], font=font_medium_bold
                )
            elif face.LAYOUT is Layout.FLIP:
                flip_image = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
                flip_draw = ImageDraw.Draw(flip_image)

                draw.text((MARGIN, MARGIN), f'> {face.NAME[0]}', font=font_bold)
                text_len = draw.textlength(face.MANA_COST[0], font=font_bold)
                draw.text(
                    (WIDTH - MARGIN - text_len, MARGIN),
                    face.MANA_COST[0],
                    font=font_bold
                )
                draw.text(
                    (MARGIN, INCH * 0.875), face.TYPE_LINE[0], font=font_medium_bold
                )

                if face.ORACLE_TEXT:
                    draw.text(
                        (MARGIN + 80, INCH * 0.33),
                        face.ORACLE_TEXT[0],
                        font=font_medium
                    )
                    flip_draw.text(
                        (MARGIN + 80, INCH * 0.33 + CENTER_GAP + BOTTOM_OFFSET),
                        face.ORACLE_TEXT[1],
                        font=font_medium
                    )

                if face.POWER and face.TOUGHNESS:
                    creature_text = f'({face.POWER[0]}/{face.TOUGHNESS[0]})'
                    text_len = draw.textlength(creature_text, font=font_bold)
                    draw.text(
                        (WIDTH - MARGIN - text_len, INCH * 0.875),
                        creature_text,
                        font=font_bold
                    )
                    creature_text = f'({face.POWER[1]}/{face.TOUGHNESS[1]})'
                    text_len = draw.textlength(creature_text, font=font_bold)
                    flip_draw.text(
                        (
                            WIDTH - MARGIN - text_len,
                            INCH * 0.875 + CENTER_GAP + BOTTOM_OFFSET * 1.5
                        ),
                        creature_text,
                        font=font_bold
                    )

                flip_draw.text(
                    (MARGIN, MARGIN + CENTER_GAP + BOTTOM_OFFSET),
                    f'> {face.NAME[1]}',
                    font=font_bold
                )
                flip_draw.text(
                    (MARGIN, INCH * 0.875 + CENTER_GAP + BOTTOM_OFFSET * 1.5),
                    face.TYPE_LINE[1],
                    font=font_medium_bold
                )
                flip_image = flip_image.rotate(180)
                card_img.paste(flip_image, mask=flip_image)

            if face.PATH == f"{card.SET_CODE}-{card.CARD_NUMBER}-00":
                draw.text(
                    (MARGIN, HEIGHT - MARGIN - BOTTOM_OFFSET),
                    f'{card.CARD_NUMBER}/{card.SET_COUNT} {card.RARITY.name}\n{card.SET_CODE} >{card.ARTIST}',
                    font=font_small
                )

                proxy_text = 'LostQuasar Proxy'
                text_len = draw.textlength(proxy_text, font=font_small_ital)
                draw.text(
                    (WIDTH - MARGIN - text_len, HEIGHT - MARGIN - 60),
                    proxy_text,
                    font=font_small_ital
                )

            if face.POWER and face.TOUGHNESS and face.LAYOUT is not Layout.FLIP:
                creature_text = f'({face.POWER[0]}/{face.TOUGHNESS[0]})'
                text_len = draw.textlength(creature_text, font=font_bold)
                draw.text(
                    (WIDTH - MARGIN - text_len, HEIGHT - MARGIN - (90 + 60 + 10)),
                    creature_text,
                    font=font_bold
                )

            card_img.save(f'cards/{face.PATH}.png')
            GEN_COUNT += 1

print(f"Downloaded: {DOWN_COUNT} art crops")
print(f"Enhanced: {ENHANCE_COUNT} art crops")
print(f"Ascii'd: {ASCII_COUNT} art crops")
print(f"Generated: {GEN_COUNT} cards")
