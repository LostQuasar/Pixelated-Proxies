import os
import random
from subprocess import Popen
from textwrap import wrap
import time
from typing import Optional
import requests
from enum import Enum
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from card_info import *

INCH = 900
WIDTH, HEIGHT = int(2.5 * INCH), int(3.5 * INCH)
DOWN_COUNT = 0
ENHANCE_COUNT = 0
ASCII_COUNT = 0
GEN_COUNT = 0


def download_art_crop(face: CardFace):
    global DOWN_COUNT
    img = Image.open(requests.get(face.ART, stream=True).raw)
    img.save(f'art_crops/{face.PATH}.jpg')

    time.sleep(0.4)
    generate_ascii_art(face)


def generate_ascii_art(face: CardFace):
    global ASCII_COUNT
    width = 130 if not face.LAYOUT is Layout.SPLIT else 184
    Popen(
        f'image-to-ascii art_crops/{face.PATH}.jpg -w{width} -b0 -o ascii/{face.PATH}.png',
        shell=True
    )
    ASCII_COUNT += 1
    time.sleep(0.1)


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

            elif not os.path.exists(f"ascii/{face.PATH}.png"):
                generate_ascii_art(face)

            card_img = Image.new('RGB', (WIDTH, HEIGHT), (0, 0, 0))

            with Image.open(f'ascii/{face.PATH}.png') as ascii_art:
                ascii_art = ImageEnhance.Color(ascii_art).enhance(1.3)
                ascii_art = ImageEnhance.Contrast(ascii_art).enhance(1.2)
                vert_offset = 0
                hor_offset = 0
                if face.LAYOUT is Layout.SPLIT:
                    ascii_art = ascii_art.rotate(90, expand=True)
                    vert_offset = 575 - 80
                    hor_offset = 225
                ascii_art = ascii_art.resize(
                    (ascii_art.width * 2, ascii_art.height * 2),
                    resample=Image.Resampling.NEAREST
                )
                card_img.paste(
                    ascii_art,
                    (
                        int((WIDTH / 2) - (ascii_art.width / 2) - hor_offset),
                        int((HEIGHT / 2) - (ascii_art.height / 2) - 575 + vert_offset)
                    )
                )

            draw = ImageDraw.Draw(card_img)
            if face.LAYOUT is Layout.NORMAL or face.LAYOUT is Layout.TRANSFORM:
                draw.text((INCH / 6, INCH / 6), f'> {face.NAME[0]}', font=font_bold)
                text_len = draw.textlength(face.MANA_COST[0], font=font_bold)
                draw.text(
                    (WIDTH - INCH / 6 - text_len, INCH / 6),
                    face.MANA_COST[0],
                    font=font_bold
                )

                draw.text(
                    (INCH / 6, INCH * 2), face.TYPE_LINE[0], font=font_medium_bold
                )

                if face.ORACLE_TEXT:
                    draw.text(
                        (INCH / 4, INCH * 2.15), face.ORACLE_TEXT[0], font=font_medium
                    )
                if face.FLAVOR_TEXT:
                    draw.text(
                        (
                            INCH / 4,
                            INCH * 2.15
                            + (face.ORACLE_TEXT[0].count('\n') + 1.5)
                            * font_medium.size
                        ),
                        face.FLAVOR_TEXT,
                        font=font_ital
                    )
            elif face.LAYOUT is Layout.SPLIT:
                rot_image = Image.new('RGBA', (HEIGHT, WIDTH), (0, 0, 0, 0))
                rot_draw = ImageDraw.Draw(rot_image)
                rot_draw.text(
                    (INCH / 6 + 150, INCH / 6), f'> {face.NAME[0]}', font=font_bold
                )
                rot_draw.text(
                    (INCH / 12 + HEIGHT / 2, INCH / 6),
                    f'> {face.NAME[1]}',
                    font=font_bold
                )
                text_len = draw.textlength(face.MANA_COST[0], font=font_bold)
                rot_draw.text(
                    (HEIGHT / 2 - INCH / 12 - text_len, INCH / 6),
                    face.MANA_COST[0],
                    font=font_bold
                )
                text_len = draw.textlength(face.MANA_COST[1], font=font_bold)
                rot_draw.text(
                    (HEIGHT - INCH / 6 - text_len, INCH / 6),
                    face.MANA_COST[1],
                    font=font_bold
                )
                rot_draw.text(
                    (INCH / 6 + 150, INCH * 1.625),
                    face.TYPE_LINE[0],
                    font=font_medium_bold
                )
                rot_draw.text(
                    (INCH / 12 + HEIGHT / 2, INCH * 1.625),
                    face.TYPE_LINE[1],
                    font=font_medium_bold
                )

                if face.ORACLE_TEXT:
                    rot_draw.text(
                        (INCH / 6 + 150, INCH * 1.75),
                        face.ORACLE_TEXT[0],
                        font=font_medium
                    )
                    rot_draw.text(
                        (HEIGHT / 2 + INCH / 12, INCH * 1.75),
                        face.ORACLE_TEXT[1],
                        font=font_medium
                    )
                rot_image = rot_image.rotate(90, expand=True)
                card_img.paste(rot_image, mask=rot_image)
            elif face.LAYOUT is Layout.ADVENTURE:
                draw.text((INCH / 6, INCH / 6), f'> {face.NAME[0]}', font=font_bold)
                text_len = draw.textlength(face.MANA_COST[0], font=font_bold)
                draw.text(
                    (WIDTH - INCH / 6 - text_len, INCH / 6),
                    face.MANA_COST[0],
                    font=font_bold
                )

                draw.text(
                    (INCH / 6, INCH * 2), face.TYPE_LINE[0], font=font_medium_bold
                )

                if face.ORACLE_TEXT:
                    draw.text(
                        (WIDTH / 2 + INCH / 12, INCH * 2.15),
                        face.ORACLE_TEXT[0],
                        font=font_medium
                    )

                draw.text(
                    (INCH / 6, INCH * 2.15), f'{face.NAME[1]}', font=font_medium_bold
                )
                text_len = draw.textlength(face.MANA_COST[1], font=font_medium_bold)
                draw.text(
                    (WIDTH / 2 - INCH / 12 - text_len, INCH * 2.15),
                    face.MANA_COST[1],
                    font=font_medium_bold
                )

                draw.text(
                    (INCH / 6, INCH * 2.25), face.TYPE_LINE[1], font=font_medium_bold
                )

                if face.ORACLE_TEXT:
                    draw.text(
                        (INCH / 6, INCH * 2.4), face.ORACLE_TEXT[1], font=font_medium
                    )

            if face.PATH == f"{card.SET_CODE}-{card.CARD_NUMBER}-00":
                draw.text(
                    (INCH / 6, HEIGHT - INCH / 6 - 120),
                    f'{card.CARD_NUMBER}/{card.SET_COUNT} {card.RARITY.name}\n{card.SET_CODE} >{card.ARTIST}',
                    font=font_small
                )

                proxy_text = 'LostQuasar Proxy'
                text_len = draw.textlength(proxy_text, font=font_small_ital)
                draw.text(
                    (WIDTH - INCH / 6 - text_len, HEIGHT - INCH / 6 - 60),
                    proxy_text,
                    font=font_small_ital
                )

            if face.POWER and face.TOUGHNESS:
                creature_text = f'({face.POWER}/{face.TOUGHNESS})'
                text_len = draw.textlength(creature_text, font=font_bold)
                draw.text(
                    (WIDTH - INCH / 6 - text_len, HEIGHT - INCH / 6 - (90 + 60 + 10)),
                    creature_text,
                    font=font_bold
                )

            card_img.save(f'cards/{face.PATH}.png')
            GEN_COUNT += 1

print(f"Downloaded: {DOWN_COUNT} art crops")
print(f"Enhanced: {ENHANCE_COUNT} art crops")
print(f"Ascii'd: {ASCII_COUNT} art crops")
print(f"Generated: {GEN_COUNT} cards")
