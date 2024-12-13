from enum import Enum
from textwrap import wrap
from typing import List, Optional
import requests


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

class CardFace:
    NAME: str
    MANA_COST: str
    ORACLE_TEXT: Optional[str]
    FLAVOR_TEXT: Optional[str]
    TYPE_LINE: str
    POWER: Optional[str]
    TOUGHNESS: Optional[str]
    ART: str
    PATH: str

    def __init__(self, card_face, path):
        self.NAME = card_face['name']
        self.MANA_COST = card_face['mana_cost']
        self.ART = card_face['image_uris']['art_crop']
        self.PATH = path
        self.TYPE_LINE = card_face['type_line']
        if 'oracle_text' in card_face:
            oracle_text = []
            for line in card_face['oracle_text'].split('\n'):
                line = '\n'.join(wrap(line, width=40))
                oracle_text.append(line)
            oracle_text = '\n'.join(oracle_text)
        else:
            oracle_text = None
        self.ORACLE_TEXT = oracle_text

        if 'flavor_text' in card_face:
            flavor_text = []
            for line in card_face['flavor_text'].split('\n'):
                line = '\n'.join(wrap(line, width=40))
                flavor_text.append(line)
            flavor_text = '\n'.join(flavor_text)
        else:
            flavor_text = None
        self.FLAVOR_TEXT = flavor_text
        
        self.POWER = card_face['power'] if 'power' in card_face else None
        self.TOUGHNESS = card_face['toughness'] if 'toughness' in card_face else None


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
        self.RARITY = Rarity(card_info["rarity"])
        self.ARTIST = card_info["artist"]
        match layout:
            case Layout.NORMAL:
                self.FACES.append(CardFace(card_info, f"{self.SET_CODE}-{self.CARD_NUMBER}-00"))
            case Layout.TRANSFORM:
                i = 0
                for face in card_info['card_faces']:
                    self.FACES.append(CardFace(face, f"{self.SET_CODE}-{self.CARD_NUMBER}-{str(i).zfill(2)}"))
                    i += 1
            case Layout.SPLIT:
                self.FACES.append(CardFace(card_info, f"{self.SET_CODE}-{self.CARD_NUMBER}-00"))

    def get_set_count(self, code):
        SET_URL = f"https://api.scryfall.com/sets/{code}"
        set_count = requests.get(SET_URL).json()['card_count']
        return set_count
