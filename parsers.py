import functools
import json
import os
import re
import itertools
from utils import consumeTokens, popArrayAfterSearch, popArrayTill, safeIndex
import logging
from constants import *

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler("debug.log", "w"),
        logging.StreamHandler()
    ]
)
_levels = []
log = logging.getLogger()


def getLog(type):
    global log
    _levels.append(type)
    log = logging.getLogger(".".join(_levels))


def checkoutLog(type):
    global log
    while (_levels.pop() != type):
        continue
    log = logging.getLogger(".".join(_levels))


PLUGINS = []


def useLog(type):
    def outer(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            getLog(type)
            result = func(*args, **kwargs)
            checkoutLog(type)
            return result
        return inner
    return outer


def register(func):
    """Register a function as a plug-in"""
    PLUGINS.append(func)
    return func


@register
@useLog("repeat")
def repeatToken(head, tokens):
    join = " ".join(tokens[0:2])
    if (join not in "Do this"):
        return None
    consumeTokens(tokens, 2)
    return {
        'type': "Repeat",
        'amount': tokens.pop(0)
    }


@register
def changeCard(head, tokens):
    if (head != change and head.capitalize() != change):
        return None
    tokens.pop(0)
    effect = {
        'type': 'ChangeCard'
    }
    if (tokens[0] == its):
        effect['target'] = 'context'
    elif (tokens[0] == this):
        effect['target'] = 'this'
    # parse what
    if (cost in tokens):
        effect['attribute'] = 'cost'
        effect['new'] = tokens[safeIndex(tokens, to)+1]
    popArrayAfterSearch(tokens, ".")
    return effect


@register
def parseTriggerEffects(head, tokens):
    if head not in triggerEffects:
        return None
    tokens.pop(0)
    return {
        'type': head,
        'effects': parseIffEffect(tokens)
    }


@register
def triggerPhaseOfTurnToken(head, tokens):
    join = " ".join(tokens[0:3])
    if (join not in stateOfTurn):
        return None
    turnCondition = popArrayAfterSearch(tokens, ",")
    # skip of
    user = turnCondition[4]
    when = "current"
    if (turnCondition[5] == "next"):
        when = "next"
    return {
        'type': join,
        'user': user,
        'when': when,
        'effects': parseSubEffect(tokens)
    }


@register
def parseOtherwise(head, tokens):
    if (head != otherwise):
        return None
    popArrayAfterSearch(tokens, ",")
    return {
        'type': otherwise,
        'effects': parseSubEffect(tokens)
    }


@register
@useLog("variableEquals")
def variableEquals(head, tokens):
    log.debug("head: %s in %s", head, variableEffects)
    if (head not in variableEffects):
        return None
    log.info("Found variable definition %s", tokens)
    tokens.pop(0)
    return {
        'type': 'VariableDefinition',
        'variable': head,
        'value': popArrayAfterSearch(tokens, endEffectToken)
    }


@register
@useLog(whenever)
def wheneverToken(head, tokens):
    if (head != whenever and head.capitalize() != whenever):
        return None
    log.info("Entered whenever %s", tokens)
    return {
        'type': whenever,
        "effects": parseIffEffect(tokens)
    }


@useLog(discard)
@register
def discardToken(head, tokens):
    if (head != discard and head.capitalize() != discard):
        return None
    log.info("Entered discard tokens %s", tokens)
    tokens.pop(0)
    return {
        'type': discard,
        'effects': parseDiscard(tokens)
    }


def parseDiscard(tokens):
    effect = {
        'cardsToDiscard': tokens[0],
        'effects': []
    }
    popArrayTill(tokens, 5)
    if (tokens[0] == andd or tokens[0] == endEffectToken):
        tokens.pop(0)
        effect['effects'] = parseSubEffect(tokens)
    return effect


@register
def recoverToken(head, tokens):
    if (head != recover and head.capitalize() != recover):
        return None
    tokens.pop(0)
    return {
        'type': recover,
        'effect': parseRecover(tokens)
    }


def parseRecover(tokens):
    effect = {}
    effect['amount'] = tokens.pop(0)
    effect['resource'] = tokens.pop(0)
    tokens.pop(0)
    return effect


@register
@useLog(fusion)
def fusionToken(head, tokens):
    if (head != fusion):
        return None
    log.info("Entering fusion with %s", tokens)
    # Fusion:
    consumeTokens(tokens, 2)
    types = popArrayAfterSearch(tokens, "\n")
    return {
        'type': fusion,
        'cardTypes': types
    }


@register
@useLog(evolve)
def evolveToken(head, tokens):
    if (head != evolve and head.capitalize() != evolve):
        return None
    log.info("Entering evolve with %s", tokens)
    tokens.pop(0)
    return {
        "type": evolve,
        "effects": consumeTokens(tokens, 2)
    }


@register
@useLog("removal")
def removalToken(head, tokens):
    if (head != destroy and head != banish):
        return None
    log.info("Entering removal with %s", tokens)
    tokens.pop(0)
    return {
        "type": head,
        "effects": parseRemoval(tokens)
    }


@register
@useLog(draw)
def drawToken(head, tokens):
    if (head != draw and head.capitalize() != draw):
        return None
    log.info("Entering draw with %s", tokens)
    tokens.pop(0)
    amount = tokens.pop(0)
    tokens.pop(0)
    return {
        "type": head,
        "amount": amount
    }


def parseRemoval(tokens):
    effect = {
        'quantifier': tokens[0],
        'user': tokens[1],
        'targets': tokens[2]
    }
    return effect


@register
@useLog(summon)
def summonToken(head, tokens):
    if (head != summon and head.capitalize() != summon):
        return None
    log.info("Entered with tokens %s", tokens)
    tokens.pop(0)
    result = {
        "type": summon,
        "effects": parseCards(tokens)
    }
    return result


@register
@useLog(put)
def putToken(head, tokens):
    if (head != put and head.capitalize() != put):
        return None
    intoStopWord = "into"
    log.info("Entered Put Token %s", tokens)
    tokens.pop(0)
    units = parseCards(tokens, stopWord=intoStopWord)
    log.debug("Left parse units ", tokens)
    destinationList = popArrayTill(tokens, 2)
    log.debug("Checking where to put units ", units)
    log.debug("DestinationList ", destinationList)
    if (hand in destinationList):
        destination = hand
    elif (deck in destinationList):
        destination = deck
    else:
        destination = destinationList
    return {
        "type": put,
        "effects": units,
        "destination": destination
    }


@register
@useLog(give)
def giveToken(head, tokens):
    if (head != give and head.capitalize() != give):
        return None
    log.info("Entered give %s", tokens)
    tokens.pop(0)
    effect = {
        "type": give,
        "effects": []
    }
    if (safeIndex(tokens, to) >= 0):
        effectTokens = popArrayAfterSearch(tokens, to)
        effect['effects'].append(parseGain(effectTokens))
    target = ""
    # find targets then find the effect
    while len(tokens) > 0:
        token = tokens.pop(0)
        if (token == "it"):
            effect['target'] = "parent"
            effect["effects"].append(parseGain(tokens))
        elif (token == "all"):
            if (token[0] == "allied" or (" ".join(tokens[0:1]) == "other allied")):
                effect['target'] = parseCards(tokens)
        elif (token == "your" or (" ".join(tokens[0:2]) == "the enemy leader")):
            target = leader
            user = "self" if token == "your" else "enemy"
            popArrayAfterSearch(tokens, effect)
        else:
            # Likely encountered an effect
            break
    return effect


@register
@useLog(gain)
def gainToken(head, tokens):
    if (head != gain and head.capitalize() != gain):
        return None
    log.info("Entered gain %s", tokens)
    tokens.pop(0)
    return {
        "type": gain,
        "effects": parseGain(tokens),
    }


@register
@useLog(restore)
def restoreToken(head, tokens):
    if (head != restore and head.capitalize() != restore):
        return None
    tokens.pop(0)
    return {
        "type": restore,
        "effects": changeHealth(tokens, defense)
    }


@register
@useLog(deal)
def dealToken(head, tokens):
    if (head != deal and head.capitalize() != deal):
        return None
    tokens.pop(0)
    return {
        "type": deal,
        "effects": changeHealth(tokens, damage)
    }


@register
@useLog(then)
def thenToken(head, tokens):
    if (head != then.capitalize()):
        return None
    log.info("Starting Then with %s", tokens)
    tokens.pop(0)
    if (tokens[0] == ","):
        tokens.pop(0)
    return {
        "type": then.capitalize(),
        "effects": parseSubEffect(tokens)
    }


@register
@useLog(iff)
def ifToken(head, tokens):
    if (head != iff and head.capitalize() != iff):
        return None
    log.info("Starting if with %s", tokens)
    tokens.pop(0)
    return {
        "type": iff,
        "effects": parseIffEffect(tokens)
    }


def parseIffEffect(tokens):
    conditionEffect = parseCondition(tokens)
    endIndex = safeIndex(tokens, endEffectToken)
    if (endIndex >= 0):
        tokens = popArrayTill(tokens, endIndex)
    log.info("Parsing if subeffect %s", tokens)
    thenEffect = parseSubEffect(tokens)
    return {
        'conditions': conditionEffect,
        'then': thenEffect
    }


@useLog(type="condition")
def parseCondition(tokens):
    log.info("Entered conditions with tokens %s", tokens)
    conditionTokens = popArrayAfterSearch(tokens, ",")
    log.info("Condition Tokens %s", conditionTokens)
    log.info("Tokens after Popping %s", tokens)
    conditions = []
    if isStartName(conditionTokens[0]):
        conditionTokens.pop(0)
        effect = {
            'type': 'CheckActiveState',
            'state': extractNameFromStartName(conditionTokens),
            'stateEqualTo': True
        }
        if (" ".join(conditionTokens[0:1]) in "is not"):
            print()
            effect['stateEqualTo'] = False
        conditions.append(effect)
    elif " ".join(conditionTokens[0:2]) == "at least":
        conditions.append({
            'type': 'CheckNumericState',
            'amount': consumeTokens(conditionTokens, 1),
            'state': popArrayAfterSearch(conditionTokens, ",")
        })
    elif " ".join(conditionTokens[0:4]) == "you have more evolution":
        conditions.append({
            'type': 'CheckEvolutionHigherThanOpponent',

        })
    elif " ".join(conditionTokens[0:1]) == "you have":
        conditions.append({
            'type': 'CheckNumericState2',
            'state': conditionTokens[2:]
        })
    elif conditionTokens[0] == "whenever":
        conditions.append({
            'type': 'WheneverAction',
            'state': conditionTokens[2:]
        })
    elif safeIndex(conditionTokens, "fused") >= 0:
        amount = 1
        if (conditionTokens[0].isnumeric()):
            exit()
            amount = conditionTokens[0].isnumeric()
        elif (" ".join(conditionTokens[0:3]) in "fused with at least"):
            consumeTokens(conditionTokens, 4)
            amount = conditionTokens.pop(0)
        conditions.append({
            'type': 'FusionAction',
            'amountToTrigger': amount
        })
    if len(conditionTokens) > 0 and conditionTokens[0] == orr:
        log.info("Found OR condition %s", conditionTokens)
        consumeTokens(conditionTokens, 1)
        conditions.append({
            'type': 'IfOr'
        })
        OrCondition = parseCondition(conditionTokens)[0]
        # Wrait or Vengence is Active
        if(OrCondition['type'] == 'CheckActiveState'):
            OrCondition['stateEqualTo'] = conditions[0]['stateEqualTo']
        conditions.append(OrCondition)
    return list(conditions)


@useLog("changeHealth")
def changeHealth(tokens, type=None):
    effect = {
        'amount': 0,
        'targets': "",
        'times': 1,
        'and': {
        }
    }

    amountIndex = tokens.index(type) - 1
    effect['amount'] = tokens[amountIndex]
    insteadIndex = safeIndex(tokens, "instead")
    if (insteadIndex > 0):
        effect['type'] = 'DamageInstead'
        popArrayTill(tokens, insteadIndex)
        return effect
    toIndex = tokens.index(to)
    quantifer = tokens[toIndex + 1]
    effect['quantifer'] = quantifer
    nextTarget = tokens[toIndex + 2]
    if (nextTarget == follower):
        effect['targets'] = nextTarget
        popArrayTill(tokens, toIndex + 2)
    if (tokens[toIndex + 2] == "other"):
        effect['targets'] = 'followers'
        effect['exceptions'] = 'other'
        popArrayTill(tokens, toIndex + 4)
    else:
        if (tokens[toIndex + 2] == endEffectToken):
            # enemies
            # allies
            effect['user'] = nextTarget
            effect['targets'] = 'all'
            popArrayTill(tokens, toIndex + 3)
        else:
            # allied followers
            # enemey followers
            effect['user'] = nextTarget
            effect['targets'] = tokens[toIndex + 2]
            popArrayTill(tokens, toIndex + 3)
    log.info("Damage tokens after target checks: %s", tokens)
    if len(tokens) >= 3 and tokens[0] == andd and tokens[1] == then:
        if (tokens[2] == the):
            effect['and'] = {
                'amount': effect['amount'],
                'user': tokens[3],
                'targets': "leader",
                'times': effect['times']
            }
        if (tokens[2].isnumeric()):
            effect['and'] = changeHealth(tokens, type)
    else:
        if (len(tokens) == 0):
            return effect
        else:
            log.warn("Encountered unexpected")
            log.warn(effect)
            log.warn(tokens)
    log.info("Leaving changeHealth with Tokens %s", tokens)
    return effect


@register
@useLog("parens")
def parensToken(head, tokens):
    if (head != "("):
        return None
    return {
        "type": "Parens",
        "condition": popArrayAfterSearch(tokens, ")")
    }


@useLog("statChange")
def parseStatChange(tokens, gainStack):
    log.info("Entering stat change %s", tokens)
    gain = {}
    while len(tokens) > 0:
        token = tokens.pop(0)
        if (token == increase or token == decrease):
            gain['type'] = 'StatChange'
            gain['operation'] = token
        if (token.isnumeric()):
            gain["amount"] = token
        if (token == attackHealthSeperator):
            gainStack.append(gain)
            gain = {}
            gain['type'] = 'StatChange'
            gainStack.append(gain)


@useLog("parseGain")
def parseGain(tokens):
    gainStack = []
    while len(tokens) > 0:
        token = tokens[0]
        log.info("Starting with Token %s", token)
        if (token == increase or token == decrease):
            parseStatChange(tokens, gainStack)
        elif (isStartName(token)):
            tokens.pop(0)
            gain = {}
            gain['type'] = extractNameFromStartName(tokens)
            gainStack.append(gain)
        elif (" ".join(tokens[0:3]) in "an empty play point"):
            gain = {}
            gain['type'] = 'An empty play point'
            gainStack.append(gain)
            popArrayAfterSearch(tokens, "point")
        elif (" ".join(tokens[0:3]) in the_ability_to_evolve):
            gain = {}
            gain['type'] = '0 EP Evolve'
            gainStack.append(gain)
            popArrayAfterSearch(tokens, "points")
        else:
            log.warn("Found Unknown %s", tokens)
            gain = {
                'type': 'Unknown',
                'tokens': popArrayAfterSearch(tokens, ".")
            }
            break
    return gainStack


def isStartName(token):
    return token == startName


def extractNameFromStartName(tokens):
    name = popArrayAfterSearch(tokens, endName)
    name.pop()
    return " ".join(name)


@useLog(type="parseCards")
def parseCards(tokens, quantifier=None, stopWord=endEffectToken):
    log.info("Entered with tokens: %s", tokens)
    units = []
    unit = {}
    stop = {andd, stopWord, andList}
    quantifiers = {"an", "a", "all", "allied"}
    specifics = {"different", "random"}
    while len(tokens) > 0:
        token = tokens.pop(0)
        if (token in quantifiers or token.isnumeric()):
            log.debug("Setting quantifiers in parseCards %s", token)
            unit['quantifer'] = token
        elif ("craft" in token):
            unit['faction'] = token
            unit['type'] = getCardType(tokens.pop(0))
        elif token in traits:
            unit['trait'] = token
            unit['type'] = getCardType(tokens.pop(0))
        elif (isStartName(token)):
            unit["card_name"] = extractNameFromStartName(tokens)
            unit["type"] = "NamedCard"
            units.append(unit)
            unit = {}
            if (len(tokens) > 0 and tokens[0] not in stop):
                break
        elif (getCardType(token) != None):
            unit['type'] = token
            units.append(unit)
        elif (token in specifics):
            if (token == random):
                unit['random'] = True
            if (token == "different"):
                unit['different'] = True
        elif (token == endEffectToken
            or token in stop
            or not isStartName(token)
                or len(tokens) == 0):
            if (token == andd):
                log.info("Card has a trigger %s", tokens)
                unit['effects'] = parseSubEffect(tokens)
            if (token == endEffectToken):
                break
            else:
                break
        else:
            log.debug("encountered else %s, %s", token)
    return units


def getCardType(type):
    if type in "followers":
        return "Follower"
    if type in "cards":
        return "Card"
    if type in "spells":
        return "spell"
    if type in "amulets":
        return "amulet"
    if type[0].isupper():
        return "NamedCard"
    return None


@useLog(type="subeffect")
def parseSubEffect(tokens):
    log.info("Parsing subeffects with Tokens %s", tokens)
    effects = []
    stack = []
    while len(tokens) > 0:
        token = tokens.pop(0)
        stack.append(token)
        if (token == newLineToken or len(tokens) == 0):
            while (len(stack) > 0):
                subEffect = None
                log.info("Starting new loop of effect parsing")
                for subEffectParser in PLUGINS:
                    if (len(stack) == 0):
                        break
                    head = stack[0]
                    log.debug("Head %s, Stack %s, Tokens %s",
                              head, stack, tokens)
                    log.debug("Subeffect parser %s", subEffectParser.__name__)
                    subEffect = subEffectParser(head, stack)
                    if (subEffect) != None:
                        log.info("Found %s", subEffect)
                        if (subEffect['type'] == otherwise and effects[-1]['type'] == iff):
                            effects[-1]['effects']['otherwise'] = subEffect
                        elif (subEffect['type'] == "Parens"):
                            effects[-1]['limit'] = subEffect
                        else:
                            effects.append(subEffect)
                        log.debug(
                            "After subeffect stack: %s, tokens: %s", stack, tokens)
                if (subEffect == None):
                    if (len(stack) > 0):
                        stack.pop(0)
    log.info("Exiting with tokens: %s", tokens)
    return effects


@register
@useLog("alternativeCosts")
def parseAlternativeCostEffect(head, tokens, stopWord=None):
    if (head not in alternativeCosts):
        return None
    log.info("Found alternativeCost %s for with %s", head, tokens)
    effect = {
        'type': head,
    }
    costEndIndex = tokens.index(")")
    effect['cost'] = tokens[costEndIndex-1]
    popArrayAfterSearch(tokens, ")")
    # +1 for ':' and ' '
    log.info("Entering subeffect for %s", head)
    effect['effects'] = parseSubEffect(tokens)
    return effect


def splitTokens(effect):
    return re.findall(r"\[b\]|\[/b\]|\b[\w']+\b|[^\w\s]|\n", effect)


def splitEffectIntoDifferentPhases(card, effect):
    tokens = splitTokens(effect)
    effectStack = []
    for effectToken in tokens:
        effectStack.append(effectToken)
        if effectToken == newLineToken:
            card['effectTokens'].append(effectStack.copy())
            effectStack.clear()
    card['effectTokens'].append(effectStack.copy())


def splitEvolveIntoDifferentPhases(card, effect):
    card['evolveEffectTokens'] = []
    if (effect == "-" or effect == "(Same as the unevolved form, excluding Fanfare.)"):
        return

    tokens = splitTokens(effect)
    effectStack = []
    for effectToken in tokens:
        effectStack.append(effectToken)
        if effectToken == newLineToken:
            card['evolveEffectTokens'].append(effectStack.copy())
            effectStack.clear()
    card['_evolveEffectTokens'] = tokens.copy()
    card['evolveEffectTokens'].append(effectStack.copy())


@useLog("evolveEffect")
def handleEvoEffect(card):
    evoEffect = card['evoEffect_']
    splitEvolveIntoDifferentPhases(card, evoEffect)
    card['evolveEffectJson'] = []
    while (len(card['evolveEffectTokens']) > 0):
        effectStrings = card['evolveEffectTokens'].pop(0)
        effectJson = {}
        if len(effectStrings) == 0:
            continue
        if (effectStrings[0] == startName):
            effectStrings.pop(0)
        if effectStrings[0] == evolve:
            effectJson['effects'] = parseSubEffect(effectStrings[2:])
            card['evolveEffectJson'].append(effectJson)


@useLog("base")
def baseParser(card):
    log.info(card["name_"])
    log.info(card["type_"])
    card['effectTokens'] = []
    card['effectJson'] = []
    effect = card['baseEffect_']
    splitEffectIntoDifferentPhases(card, effect)
    handleEvoEffect(card)
    card['_effectTokens'] = card['effectTokens'][0:]
    while (len(card['effectTokens']) > 0):
        effectStrings = card['effectTokens'].pop(0)
        effectJson = {}
        if len(effectStrings) == 0:
            continue
        if (effectStrings[0] == startName):
            effectStrings.pop(0)
        if effectStrings[0] == fusion:
            card['effectJson'].append(fusionToken(
                effectStrings[0], effectStrings[0:]))
        if effectStrings[0] in effectsWithSubeffects:
            if (effectStrings[0] == lastword):
                log.debug("Entering last words: %s", effectStrings[3:])
                effectJson['type'] = " ".join(effectStrings[0:2])
                effectJson['effects'] = parseSubEffect(effectStrings[3:])
            else:
                effectJson['type'] = effectStrings[0]
                baseEffectString = effectStrings[2:]
                # How enhance is formatted is so weird, it acts on fanfare but
                # But uses new lines for readability
                while (len(card['effectTokens']) > 0 and card['effectTokens'][0][0] == "Enhance"):
                    baseEffectString = baseEffectString + \
                        card['effectTokens'].pop(0)
                    log.info("Modified baseEffectString %s", baseEffectString)
                effectJson['effects'] = parseSubEffect(baseEffectString)
            card['effectJson'].append(effectJson)
        if card["type_"] == 'Spell':
            card['effectJson'].append(parseSubEffect(effectStrings))
        if effectStrings[0] in staticEffects:
            effectJson['type'] = effectStrings[0]
            card['effectJson'].append(effectJson)
        if effectStrings[0] in triggerEffects:
            effectJson = parseTriggerEffects(
                effectStrings[0], effectStrings[0:])
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
        if (endOfPhase != None):
            card['effectJson'].append(endOfPhase)
        log.info("Finished iteration %s", effectStrings)
    log.info(json.dumps(card["effectJson"], indent=4))
