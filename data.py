import json
import os
from parsers import *


debug = True
discardDragonDeck = {
    127431020,
    719441010,
    128441010,
    705414010,
    126414010,
    717024010,
    124441010,
    128424010,
    124441030,
    127441020
}
testCardsId = {126441030, 126431030, 127611010, 127621030, 125641020,125131010,
               126631020, 125641010, 125841010, 127841030, 127841010, 127621020, 126411030, 128241010,
               100211030
               } + discardDragonDeck


effectDebugSearch = False
effectSearch = "if"
typeMap = {
    1: 'Follower',
    2: 'Amulet',
    3: 'Countdown Amulet',
    4: 'Spell'
}


def getCardPoolFromShadowversePortal():
    rotationCardPool = list()
    cardpool = []
    files = [
        "all"
    ]
    for file in files:
        with open(f'{os.getcwd()}/json/{file}.json', 'r') as f:
            cards = json.load(f)
            cardpool = cardpool + cards['cards']
    filterToDebug(cardpool, rotationCardPool)
    return rotationCardPool


def filterToDebug(cardpool, rotationCardPool):
    for card in cardpool:
        SVP2SVPJSON(card)
        if card['rotation_'] and (not debug or card["id_"] in testCardsId):
            if (effectDebugSearch and effectSearch not in card["org_skill_disc"].lower()):
                continue
            rotationCardPool.append(card)
    return rotationCardPool


def SVP2SVPJSON(card):
    card['id_'] = card['card_id']
    card['name_'] = card['card_name']
    card['rotation_'] = card['format_type'] == 1
    card['baseEffect_'] = card['org_skill_disc'].replace("<br>", "\n")
    card['evoEffect_'] = card['org_evo_skill_disc'].replace("<br>", "\n")
    card['type_'] = typeMap[card['char_type']]
    return card


def getCardPoolFromShadowverseJson():

    files = [
        # "Dragoncraft",
        # "Portalcraft",
        "Bloodcraft"
    ]
    for file in files:
        with open(f'{os.getcwd()}/en/{file}.json', 'r') as f:
            cardpool.append(json.load(f))

    for craft in cardpool:
        for id, card in craft.items():
            if card['rotation_'] and (not debug or card["id_"] in testCardsId):
                if (effectDebugSearch and effectSearch not in card["baseEffect_"].lower()):
                    continue
                rotationCardPool.append(card)
    return rotationCardPool

_cards = getCardPoolFromShadowversePortal()



def getCard(name):
    for card in _cards:
        if(card["card_name"] == name):
            return card

def putCardInTokenPool(card):
    None
