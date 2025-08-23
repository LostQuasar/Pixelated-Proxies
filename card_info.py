from enum import Enum
from textwrap import wrap
from typing import List, Optional
import requests, re
# COMMENT OUT TO SHOW REMINDER TEXT
REMOVAL_LINES = [
    '(You may cast either half. That door unlocks on the battlefield. As a sorcery, you may pay the mana cost of a locked door to unlock it.)',
    "(This creature can't be blocked except by creatures with flying or reach.)",
    "(Attacking doesn't cause this creature to tap.)",
    '(This creature can block creatures with flying.)'
]
REMOVAL_PATTERN = r'|'.join(map(re.escape, REMOVAL_LINES))


class Rarity(Enum):
    C = 'common'
    U = 'uncommon'
    R = 'rare'
    M = 'mythic'
    S = 'special' or 'bonus'


class Layout(Enum):
    NORMAL = 'normal'
    ADVENTURE = 'adventure'
    TRANSFORM = 'transform'
    SPLIT = 'split'
    FLIP = 'flip'
    DUAL_FACE = 'modal_dfc'
    CLASS = 'class'


class CardFace:
    NAME: list[str]
    MANA_COST: list[str]
    ORACLE_TEXT: Optional[list[str]]
    FLAVOR_TEXT: Optional[list[str]]
    TYPE_LINE: list[str]
    POWER: list[str]
    TOUGHNESS: list[str]
    ART: str
    PATH: str
    LAYOUT: Layout
    FULL_ART: bool

    def __init__(self, card_face, path, layout):
        self.NAME = str(card_face['name']).split(' // ')
        self.LAYOUT = layout
        self.MANA_COST = str(card_face['mana_cost']).split(' // ')
        self.ART = card_face['image_uris']['art_crop']
        self.PATH = path
        self.TYPE_LINE = str(card_face['type_line']).split(' // ')
        DEFAULT_WIDTH = 44
        HOR_SPLIT_WIDTH = 28
        VER_SPLIT_WIDTH = 22

        if 'card_faces' in card_face:
            oracle_text = []
            for face in card_face['card_faces']:
                face_text = []
                for line in face['oracle_text'].split('\n'):
                    line = re.sub(REMOVAL_PATTERN, '', line)
                    width = DEFAULT_WIDTH
                    if layout is Layout.SPLIT:
                        width = HOR_SPLIT_WIDTH
                    if layout is Layout.ADVENTURE:
                        width = VER_SPLIT_WIDTH
                    line = '\n'.join(wrap(line, width=width))
                    face_text.append(line)
                oracle_text.append('\n'.join(face_text))
        elif 'oracle_text' in card_face:
            oracle_text = []
            for line in card_face['oracle_text'].split('\n'):
                line = re.sub(REMOVAL_PATTERN, '', line)
                line = '\n'.join(wrap(line, width=DEFAULT_WIDTH))
                oracle_text.append(line + '\n')
            oracle_text = ['\n'.join(oracle_text)]
        else:
            oracle_text = None
        self.ORACLE_TEXT = oracle_text

        if 'card_faces' in card_face:
            flavor_text = []
            for face in card_face['card_faces']:
                face_text = []
                if 'flavor_text' in face:
                    for line in face['flavor_text'].split('\n'):
                        width = (
                            HOR_SPLIT_WIDTH
                            if layout is Layout.SPLIT
                            else VER_SPLIT_WIDTH
                        )
                        line = '\n'.join(wrap(line, width=width))
                        face_text.append(line)
                    flavor_text.append('\n'.join(face_text))
        elif 'flavor_text' in card_face:
            flavor_text = []
            for line in card_face['flavor_text'].split('\n'):
                line = '\n'.join(wrap(line, width=DEFAULT_WIDTH))
                flavor_text.append(line)
            flavor_text = ['\n'.join(flavor_text)]
        else:
            flavor_text = None
        self.FLAVOR_TEXT = flavor_text

        if 'full_art' in card_face and 'land' in str(self.TYPE_LINE).lower():
            self.FULL_ART = bool(card_face['full_art'])
        else:
            self.FULL_ART = False

        self.POWER = []
        self.TOUGHNESS = []
        if 'card_faces' in card_face:
            for face in card_face['card_faces']:
                if 'power' in face and 'toughness' in face:
                    self.POWER.append(face['power'])
                    self.TOUGHNESS.append(face['toughness'])
        elif 'power' in card_face and 'toughness' in card_face:
            self.POWER.append(card_face['power'])
            self.TOUGHNESS.append(card_face['toughness'])


class CardInfo:
    LAYOUT: Layout
    SET_CODE: str
    CARD_NUMBER: str
    SET_COUNT: int
    RARITY: Rarity
    ARTIST: str
    FACES: list[CardFace]

    def __init__(self, set_code, collect_num):
        CARD_URL = f"https://api.scryfall.com/cards/{set_code}/{collect_num}"
        card_info = requests.get(CARD_URL).json()
        layout = Layout(card_info['layout'])
        self.LAYOUT = layout
        self.SET_CODE = str(card_info['set']).upper()
        self.SET_COUNT = self.get_set_count(card_info['set'])
        self.CARD_NUMBER = str(card_info['collector_number']).zfill(3)
        self.FACES = []
        self.RARITY = Rarity(card_info['rarity'])
        self.ARTIST = card_info['artist']
        match layout:
            case Layout.NORMAL:
                self.FACES.append(
                    CardFace(
                        card_info, f"{self.SET_CODE}-{self.CARD_NUMBER}-00", self.LAYOUT
                    )
                )
            case Layout.TRANSFORM:
                i = 0
                for face in card_info['card_faces']:
                    self.FACES.append(
                        CardFace(
                            face,
                            f"{self.SET_CODE}-{self.CARD_NUMBER}-{str(i).zfill(2)}",
                            self.LAYOUT
                        )
                    )
                    i += 1
            case Layout.DUAL_FACE:
                i = 0
                for face in card_info['card_faces']:
                    self.FACES.append(
                        CardFace(
                            face,
                            f"{self.SET_CODE}-{self.CARD_NUMBER}-{str(i).zfill(2)}",
                            self.LAYOUT
                        )
                    )
                    i += 1
            case Layout.SPLIT:
                self.FACES.append(
                    CardFace(
                        card_info, f"{self.SET_CODE}-{self.CARD_NUMBER}-00", self.LAYOUT
                    )
                )
            case Layout.ADVENTURE:
                self.FACES.append(
                    CardFace(
                        card_info, f"{self.SET_CODE}-{self.CARD_NUMBER}-00", self.LAYOUT
                    )
                )
            case Layout.FLIP:
                self.FACES.append(
                    CardFace(
                        card_info, f"{self.SET_CODE}-{self.CARD_NUMBER}-00", self.LAYOUT
                    )
                )
            case _:
                print(f"Format {self.LAYOUT.name} from card {card_info['name']} not supported")
                exit()

                

    def get_set_count(self, code):
        SET_URL = f"https://api.scryfall.com/sets/{code}"
        set_count = requests.get(SET_URL).json()['card_count']
        return set_count
