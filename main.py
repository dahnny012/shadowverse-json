import json
import os
from data import getCardPoolFromShadowverseJson, getCardPoolFromShadowversePortal
from parsers import *
import logging


log = logging.getLogger("base")
logging.basicConfig(
                    level=logging.INFO,
                    format='[%(levelname)s] [%(name)s] - %(message)s',
                        handlers=[
                            logging.FileHandler("debug.log"),
                            logging.StreamHandler()
                        ]
                    )

rotationCardPool = getCardPoolFromShadowversePortal()

for card in rotationCardPool:
    log.info(card["name_"])
    log.info(card["type_"])
    card['effectTokens'] = []
    card['effectJson'] = []
    effect = card['baseEffect_']
    splitEffectIntoDifferentPhases(card, effect)
    handleEvoEffect(card)
    card['_effectTokens'] = card['effectTokens'][0:]
    while(len(card['effectTokens']) > 0):
        effectStrings = card['effectTokens'].pop(0)
        effectJson = {}
        if len(effectStrings) == 0:
            continue
        if effectStrings[0] == fusion:
            card['effectJson'].append(fusionToken(effectStrings[0], effectStrings[0:]))
        if effectStrings[0] in effectsWithSubeffects:
            if (effectStrings[0] == lastword):
                log.debug("Entering last words: %s", effectStrings[3:])
                effectJson['type'] = " ".join(effectStrings[0:2])
                effectJson['effects'] = parseSubEffect(effectStrings[3:])
            else:
                effectJson['type'] = effectStrings[0]
                baseEffectString = effectStrings[2:]
                ## How enhance is formatted is so weird, it acts on fanfare but 
                ## But uses new lines for readability
                while(len(card['effectTokens']) > 0 and card['effectTokens'][0][0] == "Enhance"):
                    baseEffectString = baseEffectString + card['effectTokens'].pop(0)
                    log.info("Modified baseEffectString %s", baseEffectString)
                effectJson['effects'] = parseSubEffect(baseEffectString)
            card['effectJson'].append(effectJson)
        if card["type_"] == 'Spell':
            card['effectJson'].append(parseSubEffect(effectStrings))
        if effectStrings[0] in staticEffects:
            effectJson['type'] = effectStrings[0]
            card['effectJson'].append(effectJson)
        if effectStrings[0] in triggerEffects:
            effectJson = parseTriggerEffects(effectStrings[0],effectStrings[0:])
            card['effectJson'].append(effectJson)
        if effectStrings[0] in turnSpecificEffects:
            log.debug("Found a During your Turn")
            effectJson['type'] = effectStrings[0]
            effectJson['effect'] = parseSubEffect(effectStrings[4:])
            card['effectJson'].append(effectJson)

        if effectStrings[0] in alternativeCosts:
            card['effectJson'].append(parseAlternativeCostEffect(
                effectStrings[0], effectStrings[0:]))
        endOfPhase = triggerPhaseOfTurnToken(effectStrings[0], effectStrings)
        if(endOfPhase != None):
            card['effectJson'].append(endOfPhase)
        log.info("Finished iteration %s", effectStrings)
    log.info(json.dumps(card["effectJson"], indent=4))
    with open(f'{os.getcwd()}/output/{card["name_"]}.json', 'w') as w:
        w.write(json.dumps(card, indent=4))