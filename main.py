import codecs
import os
import random
from subprocess import Popen
from textwrap import wrap
import time
import requests
from PIL import Image, ImageEnhance, ImageDraw, ImageFont, ImageOps
from card_info import *
import toml

DPI = 900
MODE_TYPE = {'pixel': 0, 'ascii': 1}

BLEED_EDGE = 0
WIDTH, HEIGHT = int(2.5 * DPI) + BLEED_EDGE, int(3.5 * DPI) + BLEED_EDGE
MARGIN = int(1 / 5 * DPI) + BLEED_EDGE
BOTTOM_OFFSET = DPI / 6
CENTER_GAP = DPI / 16
DOWN_COUNT = 0
ENHANCE_COUNT = 0
CUSTOM_COUNT = 0
GEN_COUNT = 0
BACKGROUND_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
MANA_W_COLOR = (220, 220, 121)
MANA_U_COLOR = (63, 157, 207)
MANA_B_COLOR = (127, 72, 127)
MANA_R_COLOR = (210, 82, 71)
MANA_G_COLOR = (80, 177, 111)
MANA_COLOR = {
    'W': MANA_W_COLOR,
    'U': MANA_U_COLOR,
    'B': MANA_B_COLOR,
    'R': MANA_R_COLOR,
    'G': MANA_G_COLOR
}

MODE = 'pixel'


def download_art_crop(face: CardFace):
    global DOWN_COUNT
    img = Image.open(requests.get(face.ART, stream=True).raw)
    img.save(f'art_crops/{face.PATH}.jpg')
    DOWN_COUNT += 1
    time.sleep(1)


def generate_custom_art(face: CardFace, mode):
    global CUSTOM_COUNT
    # width = 0
    if mode == MODE_TYPE['ascii']:
        if face.LAYOUT is Layout.SPLIT:
            width = int((DPI * 3.125) / (13 * 2 + 2))
        else:
            width = int((DPI * 2.25) / (13 * 2 + 2))

        Popen(
            f'image-to-ascii art_crops/{face.PATH}.jpg -w{width} -b-4 -o ascii/{face.PATH}.png',
            shell=True
        )
        time.sleep(0.4)
        with Image.open(f'ascii/{face.PATH}.png') as ascii_image:
            ascii_image = ImageEnhance.Contrast(ascii_image).enhance(1.2)
            ascii_image = ImageEnhance.Color(ascii_image).enhance(1.2)
        ascii_image.save(f'ascii/{face.PATH}.png')

    elif mode == MODE_TYPE['pixel']:
        with Image.open(f'art_crops/{face.PATH}.jpg') as art_crop:
            pixel = art_crop.resize(
                (int(art_crop.width / 8), int(art_crop.height / 8)),
                resample=Image.Resampling.HAMMING
            )

            pixel = ImageEnhance.Contrast(pixel).enhance(1.2)
            pixel = ImageEnhance.Color(pixel).enhance(1.2)

            pixel = pixel.resize(
                (int(pixel.width * 6), int(pixel.height * 6)),
                resample=Image.Resampling.NEAREST
            )
        pixel.save(f'pixel/{face.PATH}.png')

    CUSTOM_COUNT += 1


def draw_mana_cost(right_bound, top_bound, font, cost, draw):
    mana_cost = cost.strip('{}').split('}{')
    offset = 0
    mana_cost.reverse()
    for cost in mana_cost:
        if cost in MANA_COLOR.keys():
            color = MANA_COLOR[cost]
        else:
            color = TEXT_COLOR
        if cost == '':
            continue
        cost = '{' + cost + '}'
        offset += draw.textlength(cost, font=font)
        draw.text((right_bound - offset, top_bound), cost, font=font, fill=color)
        offset += 4


def draw_oracle_text(left_bound, top_bound, font_size, font, oracle_text, draw):
    oracle_text = oracle_text.split('\n')
    oracle_vert_offset = 0
    for line in oracle_text:
        offset = 0
        broken_line = re.split(r'{|}', line)
        if len(broken_line) > 1:
            for part in broken_line:
                color = TEXT_COLOR
                if len(part) == 1:
                    if part in MANA_COLOR.keys():
                        color = MANA_COLOR[part]
                    part = '{' + part + '}'
                draw.text(
                    (left_bound + offset, top_bound + oracle_vert_offset),
                    part,
                    font=font_medium,
                    fill=color
                )
                offset += draw.textlength(part, font=font_medium)
            oracle_vert_offset += size_medium + 4
        else:
            draw.text(
                (left_bound, top_bound + oracle_vert_offset),
                line,
                font=font_medium,
                fill=TEXT_COLOR
            )
            oracle_vert_offset += size_medium + 4


with open('input.csv', 'r') as file:
    size_large = 85
    size_medium = 65
    size_small = 60
    font_large = ImageFont.truetype('Hack-Bold.ttf', size_large)
    font_medium_bold = ImageFont.truetype('Hack-Bold.ttf', size_medium)
    font_medium = ImageFont.truetype('Hack-Regular.ttf', size_medium)
    font_medium_italic = ImageFont.truetype('Hack-Italic.ttf', size_medium)
    font_small = ImageFont.truetype('Hack-Regular.ttf', size_small)
    font_small_italic = ImageFont.truetype('Hack-Italic.ttf', size_small)
    title_prefix = '> '
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
                generate_custom_art(face, MODE_TYPE[MODE])

            elif not os.path.exists(f"{MODE}/{face.PATH}.png"):
                generate_custom_art(face, MODE_TYPE[MODE])

            card_img = Image.new('RGB', (WIDTH, HEIGHT), BACKGROUND_COLOR)

            with Image.open(f'{MODE}/{face.PATH}.png') as custom_art:
                vert_offset = 0
                hor_offset = 0
                if face.LAYOUT is Layout.SPLIT:
                    custom_art = custom_art.rotate(90, expand=True)
                    vert_offset = 570 - 80
                    hor_offset = 225
                if face.FULL_ART:
                    vert_offset = 500
                if face.LAYOUT is Layout.FLIP:
                    vert_offset = 570 - BOTTOM_OFFSET
                custom_art = custom_art.resize(
                    (int(custom_art.width * 3.8), int(custom_art.height * 3.8)),
                    resample=Image.Resampling.NEAREST
                )
                card_img.paste(
                    custom_art,
                    (
                        int(((WIDTH) / 2) - (custom_art.width / 2) - hor_offset),
                        int(
                            ((HEIGHT) / 2) - (custom_art.height / 2) - 570 + vert_offset
                        )
                    )
                )

            draw = ImageDraw.Draw(card_img)
            if face.LAYOUT is Layout.NORMAL or face.LAYOUT is Layout.TRANSFORM:
                draw.text(
                    (MARGIN, MARGIN),
                    title_prefix + face.NAME[0],
                    font=font_large,
                    fill=TEXT_COLOR
                )
                draw_mana_cost(
                    WIDTH - MARGIN, MARGIN, font_large, face.MANA_COST[0], draw
                )
                if not face.FULL_ART:
                    draw.text(
                        (MARGIN, DPI * 1.95),
                        face.TYPE_LINE[0],
                        font=font_large,
                        fill=TEXT_COLOR
                    )
                    if face.ORACLE_TEXT:
                        draw_oracle_text(
                            MARGIN + 80,
                            DPI * 2.1,
                            size_medium,
                            font_medium,
                            face.ORACLE_TEXT[0],
                            draw
                        )

                if face.FLAVOR_TEXT:
                    draw.text(
                        (
                            MARGIN + 80,
                            DPI * 2.1
                            + (face.ORACLE_TEXT[0].count('\n') + 1.5) * size_medium
                        ),
                        face.FLAVOR_TEXT[0],
                        font=font_medium_italic,
                        fill=TEXT_COLOR,
                        spacing=10
                    )
            elif face.LAYOUT is Layout.SPLIT:
                rot_image = Image.new('RGBA', (HEIGHT, WIDTH), (0, 0, 0, 0))
                rot_draw = ImageDraw.Draw(rot_image)
                rot_draw.text(
                    (MARGIN + BOTTOM_OFFSET, MARGIN),
                    title_prefix + face.NAME[0],
                    font=font_large,
                    fill=TEXT_COLOR
                )
                rot_draw.text(
                    (HEIGHT / 2 + CENTER_GAP, MARGIN),
                    title_prefix + face.NAME[1],
                    font=font_large
                )

                draw_mana_cost(
                    (HEIGHT - CENTER_GAP) / 2,
                    MARGIN,
                    font_large,
                    face.MANA_COST[0],
                    rot_draw
                )
                draw_mana_cost(
                    HEIGHT - MARGIN, MARGIN, font_large, face.MANA_COST[1], rot_draw
                )
                rot_draw.text(
                    (MARGIN + BOTTOM_OFFSET, DPI * 1.625),
                    face.TYPE_LINE[0],
                    font=font_medium_bold,
                    fill=TEXT_COLOR
                )
                rot_draw.text(
                    (HEIGHT / 2 + CENTER_GAP, DPI * 1.625),
                    face.TYPE_LINE[1],
                    font=font_medium_bold,
                    fill=TEXT_COLOR
                )

                if face.ORACLE_TEXT:
                    draw_oracle_text(
                        MARGIN + BOTTOM_OFFSET,
                        DPI * 1.75,
                        size_medium,
                        font_medium,
                        face.ORACLE_TEXT[0],
                        rot_draw
                    )
                    draw_oracle_text(
                        HEIGHT / 2 + CENTER_GAP,
                        DPI * 1.75,
                        size_medium,
                        font_medium,
                        face.ORACLE_TEXT[1],
                        rot_draw
                    )
                rot_image = rot_image.rotate(90, expand=True)
                card_img.paste(rot_image, mask=rot_image)
            elif face.LAYOUT is Layout.ADVENTURE:
                draw.text(
                    (MARGIN, MARGIN), title_prefix + face.NAME[0], font=font_large
                )
                draw_mana_cost(
                    WIDTH - MARGIN, MARGIN, font_large, face.MANA_COST[0], draw
                )

                draw.text(
                    (MARGIN, DPI * 1.95),
                    face.TYPE_LINE[0],
                    font=font_large,
                    fill=TEXT_COLOR
                )

                if face.ORACLE_TEXT:
                    draw_oracle_text(
                        WIDTH / 2 + CENTER_GAP,
                        DPI * 2.2,
                        size_medium,
                        font_medium,
                        face.ORACLE_TEXT[0],
                        draw
                    )
                    draw_oracle_text(
                        MARGIN,
                        DPI * 2.4,
                        size_medium,
                        font_medium,
                        face.ORACLE_TEXT[1],
                        draw
                    )
                if face.FLAVOR_TEXT:
                    draw.text(
                        (
                            WIDTH / 2 + CENTER_GAP,
                            DPI * 2.2
                            + (face.ORACLE_TEXT[0].count('\n') + 1.5)
                            * font_medium.size
                        ),
                        face.FLAVOR_TEXT[0],
                        font=font_medium_italic,
                        fill=TEXT_COLOR
                    )

                draw.text(
                    (MARGIN, DPI * 2.125),
                    title_prefix + face.NAME[1],
                    font=font_medium_bold,
                    fill=TEXT_COLOR
                )
                draw_mana_cost(
                    WIDTH / 2 - CENTER_GAP,
                    DPI * 2.125,
                    font_medium_bold,
                    face.MANA_COST[1],
                    draw
                )

                draw.text(
                    (MARGIN, DPI * 2.25),
                    face.TYPE_LINE[1],
                    font=font_medium_bold,
                    fill=TEXT_COLOR
                )
            elif face.LAYOUT is Layout.FLIP:
                flip_image = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
                flip_draw = ImageDraw.Draw(flip_image)

                draw.text(
                    (MARGIN, MARGIN),
                    title_prefix + face.NAME[0],
                    font=font_large,
                    fill=TEXT_COLOR
                )
                draw_mana_cost(
                    WIDTH - MARGIN, MARGIN, font_large, face.MANA_COST[0], draw
                )

                draw.text(
                    (MARGIN, DPI * 0.875),
                    face.TYPE_LINE[0],
                    font=font_medium,
                    fill=TEXT_COLOR
                )

                if face.ORACLE_TEXT:
                    draw.text(
                        (MARGIN + 80, DPI * 0.33),
                        face.ORACLE_TEXT[0],
                        font=font_medium,
                        fill=TEXT_COLOR
                    )
                    flip_draw.text(
                        (MARGIN + 80, DPI * 0.33 + CENTER_GAP + BOTTOM_OFFSET),
                        face.ORACLE_TEXT[1],
                        font=font_medium,
                        fill=TEXT_COLOR
                    )

                if face.POWER and face.TOUGHNESS:
                    creature_text = f'({face.POWER[0]}/{face.TOUGHNESS[0]})'
                    text_len = draw.textlength(creature_text, font=font_large)
                    draw.text(
                        (WIDTH - MARGIN - text_len, DPI * 0.875),
                        creature_text,
                        font=font_large,
                        fill=TEXT_COLOR
                    )
                    creature_text = f'({face.POWER[1]}/{face.TOUGHNESS[1]})'
                    text_len = draw.textlength(creature_text, font=font_large)
                    flip_draw.text(
                        (
                            WIDTH - MARGIN - text_len,
                            DPI * 0.875 + CENTER_GAP + BOTTOM_OFFSET * 1.5
                        ),
                        creature_text,
                        font=font_large,
                        fill=TEXT_COLOR
                    )

                flip_draw.text(
                    (MARGIN, MARGIN + CENTER_GAP + BOTTOM_OFFSET),
                    title_prefix + face.NAME[1],
                    font=font_large,
                    fill=TEXT_COLOR
                )
                flip_draw.text(
                    (MARGIN, DPI * 0.875 + CENTER_GAP + BOTTOM_OFFSET * 1.5),
                    face.TYPE_LINE[1],
                    font=font_medium,
                    fill=TEXT_COLOR
                )
                flip_image = flip_image.rotate(180)
                card_img.paste(flip_image, mask=flip_image)

            draw.text(
                (MARGIN, HEIGHT - MARGIN - size_small * 2),
                f'{card.CARD_NUMBER}/{card.SET_COUNT} {card.RARITY.name}\n{card.SET_CODE} >{card.ARTIST}',
                font=font_small,
                fill=TEXT_COLOR
            )

            txt_string = codecs.decode(
                bytes.fromhex('5962666744686e666e65204365626b6c').decode('utf-8'),
                'rot13'
            )
            text_len = draw.textlength(txt_string, font=font_small_italic)
            draw.text(
                (WIDTH - MARGIN - text_len, HEIGHT - MARGIN - size_small),
                txt_string,
                font=font_small_italic,
                fill=TEXT_COLOR
            )

            if face.POWER and face.TOUGHNESS and face.LAYOUT is not Layout.FLIP:
                creature_text = f'({face.POWER[0]}/{face.TOUGHNESS[0]})'
                text_len = draw.textlength(creature_text, font=font_large)
                draw.text(
                    (
                        WIDTH - MARGIN - text_len,
                        HEIGHT - MARGIN - (size_large + size_small + 30)
                    ),
                    creature_text,
                    font=font_large,
                    fill=TEXT_COLOR
                )

            card_img.save(f'cards/{face.PATH}.png')
            GEN_COUNT += 1

print(f"Downloaded: {DOWN_COUNT} art crops")
print(f"Customized: {CUSTOM_COUNT} arts")
print(f"Generated: {GEN_COUNT} cards")
