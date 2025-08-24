import codecs
import os
import time
import requests
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from card_info import *
from tqdm import tqdm

DPI = 900

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
PHYREXIAN = 'P'


def download_art_crop(face: CardFace):
    global DOWN_COUNT
    global LAST_FETCH

    time_since_last = time.time() - LAST_FETCH
    if time_since_last < API_DELAY:
        time.sleep(API_DELAY - time_since_last)
    img = Image.open(requests.get(face.ART, stream=True).raw)
    LAST_FETCH = time.time()

    img.save(f'../art_crops/{face.PATH}.jpg')
    DOWN_COUNT += 1

def generate_custom_art(face: CardFace):
    global CUSTOM_COUNT
    with Image.open(f'../art_crops/{face.PATH}.jpg') as art_crop:
        pixel = art_crop.resize(
            (int(art_crop.width / 8), int(art_crop.height / 8)),
            resample=Image.Resampling.HAMMING
        )

        pixel = ImageEnhance.Contrast(pixel).enhance(1.2)
        pixel = ImageEnhance.Color(pixel).enhance(1.2)

    pixel.save(f'../pixel/{face.PATH}.png')

    CUSTOM_COUNT += 1


def draw_mana_cost(right_bound, top_bound, font, cost, draw):
    offset = 0
    color_list = []
    for i in range(len(cost)):
        char = cost[::-1][i]
        if char in MANA_COLOR.keys():
            color = MANA_COLOR[char]
            if cost[::-1][i - 1] != '/':
                color_list[-1] = color
            if cost[::-1][i - 2] == PHYREXIAN:
                color_list[-1] = color
                color_list[-2] = color
                color_list[-3] = color

        elif char == '{':
            color = color_list[-1]
        else:
            color = TEXT_COLOR
        color_list.append(color)
    for i in range(len(color_list)):
        offset += draw.textlength(cost[::-1][i], font=font)
        draw.text(
            (right_bound - offset, top_bound),
            cost[::-1][i],
            font=font,
            fill=color_list[i]
        )
    return offset


def draw_oracle_text(left_bound, top_bound, font_size, font, oracle_text, draw):
    oracle_text = oracle_text.split('\n')
    oracle_vert_offset = 0
    for line in oracle_text:
        offset = 0
        broken_line = re.split(r'{|}', line)
        for part in broken_line:
            color = TEXT_COLOR
            if len(part) == 1 and part not in ['.', '(', ')']:
                if part in MANA_COLOR.keys():
                    color = MANA_COLOR[part]
                part = '{' + part + '}'
            draw.text(
                (left_bound + offset, top_bound + oracle_vert_offset),
                part,
                font=font,
                fill=color
            )
            offset += draw.textlength(part, font=font)
        oracle_vert_offset += font_size + 4


with open('../input.csv', 'r') as file:
    size_large = 85
    size_medium = 65
    size_small = 60
    font_large = ImageFont.truetype('../resources/Hack-Bold.ttf', size_large)
    font_medium_bold = ImageFont.truetype('../resources/Hack-Bold.ttf', size_medium)
    font_medium = ImageFont.truetype('../resources/Hack-Regular.ttf', size_medium)
    font_medium_italic = ImageFont.truetype('../resources/Hack-Italic.ttf', size_medium)
    font_small = ImageFont.truetype('../resources/Hack-Regular.ttf', size_small)
    font_small_italic = ImageFont.truetype('../resources/Hack-Italic.ttf', size_small)

    if not os.path.exists('../pixel'):
        os.makedirs('../pixel')
    if not os.path.exists('../art_crops'):
        os.makedirs('../art_crops')
    if not os.path.exists('../cards'):
        os.makedirs('../cards')

    for line in tqdm(file.readlines()):
        line = line.strip().split(',')
        if line[0].startswith('plst'):
            code, num = line[1].split('-')
        else:
            code, num = line

        card: CardInfo = CardInfo(code, num)

        for face in card.FACES:
            if not os.path.exists(f"../art_crops/{face.PATH}.jpg"):
                download_art_crop(face)
                generate_custom_art(face)

            elif not os.path.exists(f"../pixel/{face.PATH}.png"):
                generate_custom_art(face)

            card_img = Image.new('RGB', (WIDTH, HEIGHT), BACKGROUND_COLOR)

            title_prefix = '> '
            if 'Legendary' in face.TYPE_LINE[0]:
                title_prefix = '# '

            # PASTE IMAGE
            with Image.open(f'../pixel/{face.PATH}.png') as custom_art:
                vert_offset = 0
                hor_offset = 0

                if face.LAYOUT is Layout.SPLIT:
                    custom_art = custom_art.rotate(90, expand=True)
                    vert_offset = 570 - 80
                    hor_offset = 225

                if face.TEXTLESS:
                    vert_offset = 500

                if face.LAYOUT is Layout.FLIP:
                    vert_offset = 570 - BOTTOM_OFFSET

                if face.LAYOUT is Layout.SAGA:
                    vert_offset = 570 - BOTTOM_OFFSET + 70
                    hor_offset = -DPI * .5

                if face.LAYOUT is Layout.CLASS:
                    vert_offset = 570 - BOTTOM_OFFSET + 70
                    hor_offset = DPI * .5

                custom_art = custom_art.resize(
                    (int(custom_art.width * 22), int(custom_art.height * 22)),
                    resample=Image.Resampling.NEAREST
                )

                if 'Planeswalker' in face.TYPE_LINE[0]:
                    vert_offset = custom_art.height / 2 - (DPI * 3 / 4)

                card_img.paste(
                    custom_art,
                    (
                        int(((WIDTH) / 2) - (custom_art.width / 2) - hor_offset),
                        int(
                            ((HEIGHT) / 2) - (custom_art.height / 2) - 570 + vert_offset
                        )
                    )
                )

            # SETUP DRAW OBJECT
            draw = ImageDraw.Draw(card_img)

            # DEFAULT LAYOUT
            if face.LAYOUT in [Layout.NORMAL, Layout.TRANSFORM, Layout.DUAL_FACE]:
                offset = draw_mana_cost(
                    WIDTH - MARGIN, MARGIN, font_large, face.MANA_COST[0], draw
                )
                if draw.textlength(title_prefix + face.NAME[0], font_large) + offset > (
                    WIDTH - MARGIN * 2
                ):
                    size = font_medium_bold
                else:
                    size = font_large
                draw.text(
                    (MARGIN, MARGIN + (size_large / 2 - size.size / 2)),
                    title_prefix + face.NAME[0],
                    font=size,
                    fill=TEXT_COLOR
                )
                text_offset = 0
                if 'Planeswalker' in face.TYPE_LINE[0]:
                    text_offset = custom_art.height - DPI * (1.55)
                    loyalty = '[' + face.LOYALTY + ']'
                    loyal_len = draw.textlength(loyalty, font=font_large)
                    draw.text(
                        (WIDTH / 2 - loyal_len / 2, HEIGHT - MARGIN - DPI / 6),
                        loyalty,
                        fill=TEXT_COLOR,
                        font=font_large
                    )
                if not face.TEXTLESS:
                    type_len = draw.textlength(face.TYPE_LINE[0], font=font_large)
                    if type_len > (WIDTH - (MARGIN * 2)):
                        size = font_medium_bold
                    else:
                        size = font_large
                    draw.text(
                        (
                            MARGIN,
                            DPI * 1.95 + text_offset + (size_large / 2 - size.size / 2)
                        ),
                        face.TYPE_LINE[0],
                        font=size,
                        fill=TEXT_COLOR
                    )
                    if face.ORACLE_TEXT:
                        draw_oracle_text(
                            MARGIN + 80,
                            DPI * 2.1 + text_offset,
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
                            + text_offset
                            + (face.ORACLE_TEXT[0].count('\n') + 1.5) * size_medium
                        ),
                        face.FLAVOR_TEXT[0],
                        font=font_medium_italic,
                        fill=TEXT_COLOR,
                        spacing=10
                    )

                if face.LAYOUT == Layout.DUAL_FACE:
                    draw.text(
                        (MARGIN, HEIGHT - MARGIN - size_small * 2 - size_medium - 60),
                        '< ' + face.ALTERNATE_TYPE,
                        font=font_medium_bold,
                        fill=TEXT_COLOR
                    )

            # SPLIT LAYOUT (Ex. ROOMS)
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

            # ADVENTURE LAYOUT
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

            # FLIP LAYOUT
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
                    font=font_medium_bold,
                    fill=TEXT_COLOR
                )

                if face.ORACLE_TEXT:
                    draw.text(
                        (MARGIN + 80, MARGIN + DPI*1/8),
                        face.ORACLE_TEXT[0],
                        font=font_medium,
                        fill=TEXT_COLOR
                    )
                    flip_draw.text(
                        (MARGIN + 80, MARGIN + DPI*1/8 + CENTER_GAP + BOTTOM_OFFSET),
                        face.ORACLE_TEXT[1],
                        font=font_medium,
                        fill=TEXT_COLOR
                    )

                if face.POWER and face.TOUGHNESS:
                    creature_text = f'({face.POWER[0]}/{face.TOUGHNESS[0]})'
                    text_len = draw.textlength(creature_text, font=font_large)
                    draw.text(
                        (WIDTH - MARGIN - text_len, DPI * 0.875 - 20),
                        creature_text,
                        font=font_large,
                        fill=TEXT_COLOR
                    )
                    creature_text = f'({face.POWER[1]}/{face.TOUGHNESS[1]})'
                    text_len = draw.textlength(creature_text, font=font_large)
                    flip_draw.text(
                        (
                            WIDTH - MARGIN - text_len,
                            DPI * 0.875 + CENTER_GAP + BOTTOM_OFFSET * 1.5 - 20
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
                    font=font_medium_bold,
                    fill=TEXT_COLOR
                )
                flip_image = flip_image.rotate(180)
                card_img.paste(flip_image, mask=flip_image)

            # SAGA and CLASS LAYOUT
            if face.LAYOUT is Layout.CLASS or face.LAYOUT is Layout.SAGA:
                if face.LAYOUT is Layout.CLASS:
                    offset = WIDTH / 2 - MARGIN + 80
                else:
                    offset = 0

                draw.text(
                    (MARGIN, MARGIN),
                    title_prefix + face.NAME[0],
                    font=font_large,
                    fill=TEXT_COLOR
                )
                draw_mana_cost(
                    WIDTH - MARGIN, MARGIN, font_large, face.MANA_COST[0], draw
                )

                if face.ORACLE_TEXT:
                    draw_oracle_text(
                        MARGIN + offset,
                        MARGIN + DPI * 2 / 8,
                        size_medium,
                        font_medium,
                        face.ORACLE_TEXT[0],
                        draw
                    )
                draw.text(
                    (MARGIN, DPI * 2.95),
                    face.TYPE_LINE[0],
                    font=font_large,
                    fill=TEXT_COLOR
                )

            # DRAW BOTTOM INFO
            if True:
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
                # DRAW POWER AND TOUGHNESS FOR DEFAULT LAYOUT
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

            card_img.save(f'../cards/{face.PATH}.png')
            GEN_COUNT += 1

print(f"Downloaded: {DOWN_COUNT} art crops")
print(f"Customized: {CUSTOM_COUNT} arts")
print(f"Generated: {GEN_COUNT} cards")
