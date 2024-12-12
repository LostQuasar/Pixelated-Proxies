import os
import random
from subprocess import Popen
from textwrap import wrap
import time
import requests
from PIL import Image, ImageEnhance, ImageDraw, ImageFont

RARITY = {'common': 'C', 'uncommon': 'U', 'rare': 'R', 'mythic': 'M'}

INCH = 900
WIDTH, HEIGHT = int(2.5 * INCH), int(3.5 * INCH)


def get_set_count(code):
    SET_URL = f"https://api.scryfall.com/sets/{code}"
    set_count = requests.get(SET_URL).json()['card_count']
    return set_count


def get_info(code, num):
    CARD_URL = f"https://api.scryfall.com/cards/{code}/{num}"
    card = requests.get(CARD_URL).json()
    return card


def download_art_crop(code, num, url):
    img = Image.open(requests.get(url, stream=True).raw)
    img.save(f'art_crops/{code}-{num}.jpg')
    time.sleep(.1)


def enchance_art_crop(code, num):
    img = Image.open(f"art_crops/{code}-{num}.jpg")
    img = ImageEnhance.Brightness(img).enhance(1)
    img = ImageEnhance.Contrast(img).enhance(1.4)
    img.save(f'enhanced/{code}-{num}.jpg')
    time.sleep(.1)


def generate_ascii_art(code, num):
    Popen(
        f'image-to-ascii enhanced/{code}-{num}.jpg -w124 -b0 -o ascii/{code}-{num}.png',
        shell=True
    )
    time.sleep(.1)

def hard_wrap(s, n, indent):
    wrapped = ""
    n_next = n - len(indent)
    for l in s.split('\n'):
        first, rest = l[:n], l[n:]
        wrapped += first + "\n"
        while rest:
            next, rest = rest[:n_next], rest[n_next:]
            wrapped += indent + next + "\n"
    return wrapped

down_count=0
ascii_count=0
enhance_count=0
gen_count=0

with open('input.csv', 'r') as file:
    for line in file.readlines():
        line = line.strip().lower().split(',')
        if line[0].startswith('plst'):
            code, num = line[1].split('-')
        else:
            code, num = line

        card = get_info(code, num)
        set_count = get_set_count(code)
        
        if not os.path.exists(f"art_crops/{code}-{num}.jpg"):
            download_art_crop(code, num, card['image_uris']['art_crop'])
            enchance_art_crop(code, num)
            generate_ascii_art(code, num)
            down_count+=1
            enhance_count+=1
            ascii_count+=1

        elif not os.path.exists(f"enhanced/{code}-{num}.jpg"):
            enchance_art_crop(code, num)
            generate_ascii_art(code, num)
            enhance_count+=1
            ascii_count+=1

        elif not os.path.exists(f"ascii/{code}-{num}.png"):
            generate_ascii_art(code, num)
            ascii_count+=1

        card_img = Image.new('RGB', (WIDTH, HEIGHT), (0, 0, 0))

        with Image.open(f'ascii/{code}-{num}.png') as ascii_art:
            ascii_art = ImageEnhance.Color(ascii_art).enhance(1.2)
            ascii_art = ImageEnhance.Contrast(ascii_art).enhance(1.2)
            ascii_art = ascii_art.resize(
                (ascii_art.width * 2, ascii_art.height * 2),
                resample=Image.Resampling.NEAREST
            )
            card_img.paste(
                ascii_art,
                (
                    int((WIDTH / 2) - (ascii_art.width / 2)),
                    int((HEIGHT / 2) - (ascii_art.height / 2) - 600)
                )
            )
        font_bold = ImageFont.truetype('Hack-Bold.ttf', 90)
        font_bold_small = ImageFont.truetype('Hack-Bold.ttf', 80)
        font_medium = ImageFont.truetype('Hack-Regular.ttf', 75)
        font_ital = ImageFont.truetype('Hack-Italic.ttf', 75)
        font_small = ImageFont.truetype('Hack-Regular.ttf', 60)
        draw = ImageDraw.Draw(card_img)
        text_len = draw.textlength(
            card['mana_cost'], font=font_bold, direction='rtl', language='en'
        )
        draw.text((INCH / 6, INCH / 6), f'> {card["name"]}', font=font_bold)
        draw.text(
            (WIDTH - INCH / 6 - text_len, INCH / 6), card['mana_cost'], font=font_bold
        )
        draw.text(
            (INCH / 6, INCH * 2),
            str(card['type_line']).replace('—', '-'),
            font=font_bold_small
        )

        body_text = []
        for line in card['oracle_text'].split("\n"):
            line = "\n".join(wrap(line, width=40))
            body_text.append(line)
        body_text = "\n".join(body_text)
        draw.text((INCH / 4, INCH * 2.25), body_text, font=font_medium)
        if 'flavor_text' in card:
            draw.text(
                (INCH / 4, INCH * 2.25 + (body_text.count('\n') + 2) * 80),
                '\n'.join(wrap(card['flavor_text'], width=38,replace_whitespace=False, break_on_hyphens=False, break_long_words=False)),
                font=font_ital
            )
        draw.text(
            (INCH / 6, HEIGHT - INCH / 6 - 120),
            f'{card["collector_number"].zfill(3)}/{set_count} {RARITY[card["rarity"]]}\n{str(card["set"]).upper()} >{card["artist"]}',
            font=font_small
        )

        card_img.save(f'cards/{code}-{num}.png')
        gen_count+=1
        time.sleep(0.300 + (random.randint(0, 100) / 100))
print(f"Downloaded: {down_count} art crops")
print(f"Enhanced: {enhance_count} art crops")
print(f"Ascii'd: {ascii_count} art crops")
print(f"Generated: {gen_count} cards")
