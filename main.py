import json
import os
from parsers import *

files = [
    "Dragoncraft",
    "Portalcraft",
    "Bloodcraft"
]

cardpool = []

for file in files:
    with open(f'{os.getcwd()}/en/{file}.json', 'r') as f:
        cardpool.append(json.load(f))


rotationCardPool = list()
debug = True
testCardsId = {126441030, 126431030, 127611010, 127621030, 125641020}
effectDebugSearch = False
effectSearch = "if"

for craft in cardpool:
    for id, card in craft.items():
        if card['rotation_'] and (not debug or card["id_"] in testCardsId):
            rotationCardPool.append(card)


for card in rotationCardPool:
    if (effectDebugSearch and effectSearch not in card["baseEffect_"].lower()):
        continue
    print(card["name_"])
    print(card["type_"])
    card['effectTokens'] = []
    card['effectJson'] = []
    effect = card['baseEffect_']
    splitEffectIntoDifferentPhases(card, effect)
    for index, effectStrings in enumerate(card['effectTokens']):
        effectJson = {}
        if len(effectStrings) == 0:
            continue
        if effectStrings[0] in effectsWithSubeffects:
            if (effectStrings[0] == lastword):
                effectJson['type'] = " ".join(effectStrings[0:1])
                effectJson['effects'] = parseSubEffect(effectStrings[3:])
            else:
                effectJson['type'] = effectStrings[0]
                effectJson['effects'] = parseSubEffect(effectStrings[2:])
            card['effectJson'].append(effectJson)
        if card["type_"] == 'Spell':
            card['effectJson'].append(parseSubEffect(effectStrings))
        if effectStrings[0] in staticEffects:
            effectJson['type'] = effectStrings[0]
            card['effectJson'].append(effectJson)
        if effectStrings[0] in triggerEffects:
            effectJson['type'] = effectStrings[0]
            effectJson['effect'] = effectStrings[0:3]
            card['effectJson'].append(effectJson)

        if effectStrings[0] in turnSpecificEffects:
            print("Found a During your Turn")
            effectJson['type'] = effectStrings[0]
            effectJson['effect'] = parseSubEffect(effectStrings[4:])
            card['effectJson'].append(effectJson)

        if effectStrings[0] in alternativeCosts:
            card['effectJson'].append(parseAlternativeCostEffect(
                effectStrings[0], effectStrings))
        join = " ".join(effectStrings[0:3])
        if (join in stateOfTurn):
            effectJson['type'] = join
            effectJson['effect'] = effectStrings
            card['effectJson'].append(effectJson)
    print(json.dumps(card["effectJson"], indent=4))
