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

    time.sleep(.4)
    generate_ascii_art(face)

def generate_ascii_art(face: CardFace):
    global ASCII_COUNT
    Popen(
        f'image-to-ascii art_crops/{face.PATH}.jpg -w130 -b0 -o ascii/{face.PATH}.png',
        shell=True
    )
    ASCII_COUNT += 1
    time.sleep(.1)

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
                ascii_art = ascii_art.resize(
                    (ascii_art.width * 2, ascii_art.height * 2),
                    resample=Image.Resampling.NEAREST
                )
                card_img.paste(
                    ascii_art,
                    (
                        int((WIDTH / 2) - (ascii_art.width / 2)),
                        int((HEIGHT / 2) - (ascii_art.height / 2) - 575)
                    )
                )
            

            draw = ImageDraw.Draw(card_img)

            draw.text((INCH / 6, INCH / 6), f'> {face.NAME}', font=font_bold)

            text_len = draw.textlength(face.MANA_COST, font=font_bold)
            draw.text(
                (WIDTH - INCH / 6 - text_len, INCH / 6), face.MANA_COST, font=font_bold
            )
            
            draw.text(
                (INCH / 6, INCH * 2),
                face.TYPE_LINE,
                font=font_medium_bold
            )

            if face.ORACLE_TEXT:
                draw.text((INCH / 4, INCH * 2.15), face.ORACLE_TEXT, font=font_medium)
            if face.FLAVOR_TEXT:
                draw.text(
                    (INCH / 4, INCH * 2.15 + (face.ORACLE_TEXT.count('\n') + 1.5) * font_medium.size),
                    face.FLAVOR_TEXT,
                    font=font_ital
                )
            if face.PATH == f"{card.SET_CODE}-{card.CARD_NUMBER}-00":
                draw.text(
                    (INCH / 6, HEIGHT - INCH / 6 - 120),
                    f'{card.CARD_NUMBER}/{card.SET_COUNT} {card.RARITY.name}\n{card.SET_CODE} >{card.ARTIST}',
                    font=font_small
                )

                proxy_text = "LostQuasar Proxy"
                text_len = draw.textlength(proxy_text,font=font_small_ital)
                draw.text((WIDTH - INCH / 6 - text_len, HEIGHT - INCH / 6 -  60), proxy_text, font=font_small_ital)

            if face.POWER and face.TOUGHNESS:
                creature_text = f'({face.POWER}/{face.TOUGHNESS})'
                text_len = draw.textlength(creature_text, font=font_bold)
                draw.text(
                    (WIDTH - INCH / 6 - text_len, HEIGHT - INCH / 6 - (90 + 60 + 10)), creature_text, font=font_bold
                )
            card_img.save(f'cards/{face.PATH}.png')
            GEN_COUNT+=1

print(f"Downloaded: {DOWN_COUNT} art crops")
print(f"Enhanced: {ENHANCE_COUNT} art crops")
print(f"Ascii'd: {ASCII_COUNT} art crops")
print(f"Generated: {GEN_COUNT} cards")
