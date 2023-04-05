import functools
import json
import os
import re
import itertools
from utils import consumeTokens, popArrayAfterSearch, popArrayTill, safeIndex
import logging

bane = "Bane"
ward = "Ward"
fanfare = 'Fanfare'
lastword = 'Last'
rush = 'Rush'
endEffectToken = '.'
summon = 'Summon'
put = 'Put'
oneQuantifier = 'a'
enhance = 'Enhance'
rally = 'Rally'
draw = 'Draw'
then = 'then'
andd = 'and'
andList = ","
evolve = 'Evolve'
drain = 'Drain'
storm = 'Storm'
accel = 'Accelerate'
gain = 'Gain'
clash = "Clash"
strike = "Strike"
deal = "Deal"
damage = "damage"
to = "to"
follower = 'follower'
iff = "If"
burialRite = "Bural"
newLineToken = "\n"
increase = "+"
decrease = "-"
attackHealthSeperator = "/"
the = "the"
during = "during"
whenever = "Whenever"
thenAnd = re.compile(r'(and|\.)')
whilee = "while"
startOfTurn = "At the start"
endOfTurn = "At the end"
during = "During"
destroy = "Destroy"
banish = "Banish"
restore = "Restore"
defense = "defense"
ambush = "Ambush"
resonsance = "Resonance"
wraith = "Wrath"
vengeance = "Vengeance"
fusion = "Fusion"
recover = "Recover"
cantBeDestroyedByEffects = "Can't be destroyed by effects."
discard = "Discard"
X, Y, Z = "X", "Y", "Z"
instead = "instead"
otherwise = "Otherwise"
hand = "hand"
deck = "deck"
orr = "or"
the_ability_to_evolve = "the ability to evolve"
nott = "noy"
change = "Change"
cost = "cost"
its = "its"
this = "this"
random = "random"
give = "Give"
thisMatch = "this match"
leader = "leader"

stateConditions = {resonsance, wraith, vengeance}
staticEffects = {ward, drain, rush, storm, bane, ambush}
effectsWithSubeffects = {fanfare, lastword, strike}
additionalEffects = {deal, gain, draw}
subeffectsWithQuantitfiers = [summon, put, draw]
alternativeCosts = {enhance, accel, burialRite}
triggerEffects = {whenever}
stateOfTurn = {startOfTurn, endOfTurn}
turnSpecificEffects = {
    during
}
constantEffects = {whilee}
variableEffects = {X, Y, Z}
traits = {
    "Festive", "Officer", "Condemned", "Machina", "Academic", "Natura", "Commander", "Mysteria", "Chess", "Loot", "Levin"
}

logging.basicConfig(
                    level=logging.DEBUG,
                    format='[%(levelname)s] [%(name)s] - %(message)s'
                    )
_levels = ["base"]
log = logging.getLogger("base")


def getLog(type):
    global log
    _levels.append(type)
    log = logging.getLogger(".".join(_levels))

def checkoutLog(type):
    global log
    while(_levels.pop() != type):
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
    if (head not in variableEffects):
        return None
    log.info("Found variable definition %s", tokens)
    tokens.pop(0)
    return {
        'type': 'VariableDefinition',
        'variable': head
    }

@register
@useLog(whenever)
def wheneverToken(head, tokens):
    if (head != whenever and head.capitalize() != whenever):
        return None
    log.info("Entered whenever ", tokens)
    return {
        'type': whenever,
        "effects": parseIffEffect(tokens)
    }

@register
@useLog(discard)
def discardToken(head, tokens):
    if (head != discard and head.capitalize() != discard):
        return None
    log.info("Entered discard tokens ", tokens)
    tokens.pop(0)
    return {
        'type': discard,
        'effects': parseDiscard(tokens)
    }

def parseDiscard(head, tokens):
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
def evolveToken(head, tokens):
    if (head != evolve and head.capitalize() != evolve):
        return None
    tokens.pop(0)
    return {
        "type": evolve,
        "effects": tokens
    }

@register
def removalToken(head, tokens):
    if (head != destroy and head != banish):
        return None
    tokens.pop(0)
    return {
        "type": head,
        "effects": parseRemoval(tokens)
    }

@register
def drawToken(head, tokens):
    if (head != draw and head.capitalize() != draw):
        return None
    tokens.pop(0)
    amount = tokens.pop(0)
    tokens.pop(0)
    return {
        "type": head,
        "effects": {
            'quantifier': amount
        }
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
    if (deck in destinationList):
        destination = deck
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
    if(safeIndex(tokens, to) >= 0):
        effectTokens = popArrayAfterSearch(tokens , to)
        effect['effects'].append(parseGain(effectTokens))
    target = ""
    # find targets then find the effect
    while len(tokens) > 0:
        token = tokens.pop(0)
        if (token == "it"):
            effect['target'] = "parent"
            effect["effects"].append(parseGain(tokens))
        elif (token == "all"):
            if(token[0] == "allied" or (" ".join(tokens[0:1]) == "other allied")):
                effect['target'] = parseCards(tokens)
        elif(token == "your" or (" ".join(tokens[0:2]) == "the enemy leader")):
            target = leader
            user = "self" if token == "your" else "enemy"
            popArrayAfterSearch(tokens, effect)
        else:
            ## Likely encountered an effect
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
    log.info("Starting Then with ", tokens)
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
    conditions = []
    if conditionTokens[0] in stateConditions:
        effect = {
            'type': 'CheckActiveState',
            'state': consumeTokens(conditionTokens, 1),
            'stateIsActive': True
        }
        if (" ".join(conditionTokens[0:1]) in "is not"):
            effect['stateIsActive'] = False
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
    elif safeIndex(conditionTokens, "fused"):
        amount = 1
        if (conditionTokens[0].isnumeric()):
            amount = conditionTokens[0].isnumeric()
        conditions.append({
            'type': 'FusionAction',
            'amountToTrigger': amount
        })
    if len(conditionTokens) > 0 and conditionTokens[0] == orr:
        log.info("Found OR condition %s", conditionTokens)
        consumeTokens(conditionTokens, 1)
        conditions.append(parseCondition(conditionTokens)[0])
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
    log.info("Damage tokens after target checks: ", tokens)
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
        if (tokens[0] == endEffectToken):
            tokens.pop(0)
        else:
            log.warn("Encountered unexpected")
            log.warn(effect)
            log.warn(tokens)
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
    log.info("Entering stat change", tokens)
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
        if (token == increase or token == decrease):
            parseStatChange(tokens, gainStack)
        elif (token in staticEffects):
            gain = {}
            gain['type'] = token
            gainStack.append(gain)
            tokens.pop(0)
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

def isANameToken(token):
    partOfName = {","}
    isAProperNoun = token[0].isupper() or  token  in partOfName
    notAStaticAbility = token not in staticEffects
    return isAProperNoun and notAStaticAbility

@useLog(type="parseCards")
def parseCards(tokens, quantifier=None, stopWord=None):
    log.info("Entered with tokens: %s", tokens)
    units = []
    unitStack = []
    unit = {}
    stop = {andd, stopWord, andList}
    quantifiers = {"an", "a", "all", "allied"}
    specifics = {"different", "random"}
    while len(tokens) > 0:
        token = tokens.pop(0)
        if (token in quantifiers or token.isnumeric()):
            log.debug("Setting quantifiers in parseCards %s", token)
            unit['quantifer'] = token
        elif("craft" in token):
            unit['faction'] = token
            unit['type'] = getCardType(tokens.pop(0))
        elif token in traits:
            unit['trait'] = token
            unit['type'] = getCardType(tokens.pop(0))
        elif(isANameToken(token)):
            unitStack.append(token)
            if(token == "Lloyd"):
                unitStack = unitStack + consumeTokens(tokens, 3)
                log.debug("encountered lloyd: stack: %s", unitStack)
            
        elif(getCardType(token) != None):
            unit['type'] = token
        elif(token in specifics):
            if(token == random):
                unit['random'] = True
            if(token == "different"):
                unit['different'] = True
        if (token == endEffectToken
              or token in stop
              or not isANameToken(token)
              or len(tokens) == 0):
            if(len(unitStack) > 0):
                log.info("Unit stack", unitStack)
                unitName = " ".join(unitStack)
                unit["type"] = getCardType(unitName)
                if unit["type"] == "NamedCard":
                    unit["cardname"] = unitName
                units.append(unit)
                unitStack = []
                if(token == andd and not tokens[0][0].isupper()):
                    log.info("Card has a trigger %s", tokens)
                    unit['effects'] = parseSubEffect(tokens)
                unit = {}
        else:
            log.debug("encountered else %s, %s", token, unitStack)
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
                for subEffectParser in PLUGINS:
                    if (len(stack) == 0):
                        break
                    head = stack[0]
                    if head == endEffectToken or head == andd or head == newLineToken:
                        stack.pop(0)
                        if (len(stack) > 0):
                            head = stack[0]
                    log.debug("Head %s, Stack %s, Tokens %s", head, stack, tokens)
                    subEffect = subEffectParser(head, stack)
                    if (subEffect) != None:
                        log.info("Found %s", subEffect)
                        if (subEffect['type'] == otherwise and effects[-1]['type'] == iff):
                            effects[-1]['effects']['otherwise'] = subEffect
                        elif (subEffect['type'] == "Parens"):
                            effects[-1]['limit'] = subEffect
                        else:
                            effects.append(subEffect)
                        log.debug("After subeffect stack: %s, tokens: %s", stack, tokens)
                if (subEffect == None):
                    break
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
    # +1 for ':' and ' '
    log.info("Entering subeffect for ", head)
    effect['effects'] = parseSubEffect(tokens[costEndIndex + 2:])
    return effect


def splitEffectIntoDifferentPhases(card, effect):
    effectTokens = re.findall(r"\b[\w']+\b|[^\w\s]|\n", effect)
    effectStack = []
    for effectToken in effectTokens:
        effectStack.append(effectToken)
        if effectToken == newLineToken:
            card['effectTokens'].append(effectStack.copy())
            effectStack.clear()
    card['effectTokens'].append(effectStack.copy())
