import json
import os
import re

from utils import popArrayAfterSearch, popArrayTill, safeIndex


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
vengence = "Vengence"
fusion = "Fusion"
recover = "Recover"
cantBeDestroyedByEffects = "Can't be destroyed by effects."
discard = "Discard"
X, Y, Z = "X", "Y", "Z"
instead = "instead"
otherwise = "Otherwise"
hand = "hand"
deck = "deck"

stateConditions = {resonsance, wraith, vengence}
staticEffects = {ward, drain, rush, storm, bane, ambush}
effectsWithSubeffects = {fanfare, lastword, strike}
additionalEffects = {deal, gain, draw}
subeffectsWithQuantitfiers = [summon, put, draw]
alternativeCosts = {enhance, accel, burialRite}
triggerEffects = {whenever, whilee, whenever}
stateOfTurn = {startOfTurn, endOfTurn}
turnSpecificEffects = {
    during
}
variableEffects = {X, Y, Z}

def subEffectParsers():
    return [
        summonToken,
        putToken,
        gainToken,
        dealToken,
        ifToken,
        parseAlternativeCostEffect,
        removalToken,
        restoreToken,
        drawToken,
        evolveToken,
        recoverToken,
        discardToken,
        wheneverToken,
        variableEquals,
        parensToken,
        parseOtherwise,
        thenToken
    ]

def parseOtherwise(head, tokens):
    if (head != otherwise):
        return None
    return {
        'type': otherwise,
        "text": tokens
    }

def variableEquals(head, tokens):
    if (head not in variableEffects):
        return None
    print("Found variable definition ", tokens)
    tokens.pop(0)
    return {
        'type': 'VariableDefinition',
        'variable': head
    }


def wheneverToken(head, tokens):
    if (head != whenever and head.capitalize() != whenever):
        return None
    return {
        'type': whenever,
        "effect": parseIffEffect(tokens)
    }


def discardToken(head, tokens):
    if (head != discard and head.capitalize() != discard):
        return None
    print("Entered discard tokens ", tokens)
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


def fusionToken(head, tokens):
    if (head != fusion):
        return None
    return {
        'type': fusion,
        'cardTypes': {},
        'effectOnFused': {}
    }


def evolveToken(head, tokens):
    # print(head)
    if (head != evolve and head.capitalize() != evolve):
        return None
    tokens.pop(0)
    return {
        "type": evolve,
        "effects": tokens
    }


def removalToken(head, tokens):
    if (head != destroy and head != banish):
        return None
    tokens.pop(0)
    return {
        "type": head,
        "effects": parseRemoval(tokens)
    }


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


def summonToken(head, tokens):
    if (head != summon):
        return None
    return {
        "type": summon,
        "effects": parseUnits(tokens[1:])
    }


def putToken(head, tokens):
    if (head != put and head.capitalize() != put):
        return None
    intoStopWord = "into"
    print("Entered Put Token ", tokens)
    units = parseUnits(tokens[1:], stopWord=intoStopWord)
    stopIndex = sum(obj["_stopIndex"] for obj in units)
    popArrayTill(tokens, stopIndex)
    destinationList = popArrayAfterSearch(tokens, endEffectToken)
    destination = ""
    print("Checking where to put units ", units)
    print("destinationList ", destinationList)
    if(hand in destinationList):
        destination = hand
    if(deck in destinationList):
        destination = deck
    return {
        "type": put,
        "effects": units,
        "destination": destination
    }


def gainToken(head, tokens):
    if (head != gain and head.capitalize() != gain):
        return None
    print("Entered gain, ", tokens)
    tokens.pop(0)
    return {
        "type": gain,
        "effects": parseGain(tokens),
    }


def restoreToken(head, tokens):
    if (head != restore and head.capitalize() != restore):
        return None
    tokens.pop(0)
    return {
        "type": restore,
        "effects": changeHealth(tokens, defense)
    }


def dealToken(head, tokens):
    if (head != deal and head.capitalize() != deal):
        return None
    tokens.pop(0)
    return {
        "type": deal,
        "effects": changeHealth(tokens, damage)
    }

def thenToken(head, tokens):
    if (head != then.capitalize()):
        return None
    print("Starting Then with ", tokens)
    tokens.pop(0)
    if(tokens[0] == ","):
        tokens.pop(0)   
    return {
        "type": then.capitalize(),
        "effects": parseSubEffect(tokens)
    }
    

def ifToken(head, tokens):
    if (head != iff and head.capitalize() != iff):
        return None
    print("Starting if with ", tokens)
    tokens.pop(0)
    return {
        "type": iff,
        "effects": parseIffEffect(tokens)
    }


def parseIffEffect(tokens):
    endIfIndex = tokens.index(",") + 1
    condition = popArrayTill(tokens, endIfIndex)
    print("Found condition ", condition)
    conditionEffect = parseCondition(condition)
    endIndex = safeIndex(tokens, endEffectToken)
    if (endIndex >= 0):
        tokens = popArrayTill(tokens, endIndex)
    print("Parsing subeffect ", tokens)
    thenEffect = parseSubEffect(tokens)
    return {
        'condition': conditionEffect,
        'then': thenEffect
    }


def parseCondition(conditionTokens):
    if conditionTokens[0] in stateConditions:
        return {
            'type': 'CheckActiveState',
            'state': conditionTokens[0]
        }
    if " ".join(conditionTokens[0:2]) == "at least":
        return {
            'type': 'CheckNumericState',
            'state': conditionTokens[2:]
        }
    if " ".join(conditionTokens[0:4]) == "you have more evolution":
        return {
            'type': 'CheckEvolutionHigherThanOpponent',
        }
    if " ".join(conditionTokens[0:1]) == "you have":
        return {
            'type': 'CheckNumericState2',
            'state': conditionTokens[2:]
        }
    if conditionTokens[0] == "whenever":
        return {
            'type': 'Action',
            'state': conditionTokens[2:]
        }

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
            print("TOKENENNE?? ?? ", tokens)
            popArrayTill(tokens, toIndex + 3)
        else:
            # allied followers
            # enemey followers
            effect['user'] = nextTarget
            effect['targets'] = tokens[toIndex + 2]
            popArrayTill(tokens, toIndex + 3)
    print("damage tokens after ", tokens)
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
            print("wtf")
            print(effect)
            print(tokens)
    return effect

def parensToken(head, tokens):
    if(head != "("):
        return None
    return {
        "type": "Parens",
        "condition": popArrayAfterSearch(tokens, ")")
    }


def parseGain(tokens):
    gain = {}
    gainStack = []
    while len(tokens) > 0:
        token = tokens[0]
        if (token != increase and token != decrease and not token.isnumeric() and token != attackHealthSeperator):
            if (token in staticEffects):
                gain['type'] = token
                tokens.pop(0)
            if (" ".join(tokens[0:3]) in "an empty play point"):
                gain['type'] = 'An empty play point'
                popArrayTill(tokens, 6)
            else:
                break
        else:
            print("Got token ", token)
            if (token == increase or token == decrease):
                gain['type'] = 'StatChange'
                gain['operation'] = token
            if (token.isnumeric()):
                gain["amount"] = token
            if (token == attackHealthSeperator):
                gainStack.append(gain)
                gain = {}
                gain['type'] = 'StatChange'
            tokens.pop(0)
    gainStack.append(gain)
    gain = {}
    return gainStack


def parseUnits(tokens, quantifier=None, stopWord=None):
    print("Starting to parse units , ", tokens)
    i = 0
    units = []
    unitStack = []
    unit = {
        "type": "",
        "quantifer": quantifier,
        "unitName": "",
        "_stopIndex": ""
    }
    stop = {andd, andList, stopWord}

    while i < len(tokens):
        token = tokens[i]
        if (i == 0 and quantifier == None):
            unit["quantifer"] = token
        else:
            if (token == endEffectToken or token in (stop)):
                unitName = " ".join(unitStack)
                unit["type"] = SummonUnitOrEffect(unitName)
                if unit["type"] == "Card":
                    unit["unitName"] = unitName
                units.append(unit)
                unit['_stopIndex'] = i+1
                break
            else:
                unitStack.append(token)
        i += 1
    if i != len(tokens) and (tokens[i] == andd or token == andList):
        units.append(parseUnits(tokens[i+1:], unit['quantifer'])[0])
    return units


def SummonUnitOrEffect(unitName):
    if (len(unitName) == 0):
        return None
    return "Card" if (unitName[0].isupper() == True) else "Effect"


def parseSubEffect(tokens):
    print("Entered subeffect with tokens ", tokens)
    effects = []
    stack = []
    while len(tokens) > 0:
        token = tokens.pop(0)
        stack.append(token)
        if (token == newLineToken or len(tokens) == 0):
            while (len(stack) > 0):
                subEffect = None
                for subEffectParser in subEffectParsers():
                    if (len(stack) == 0):
                        break
                    head = stack[0]
                    if head == endEffectToken or head == andd or head == newLineToken:
                        stack.pop(0)
                        if (len(stack) > 0):
                            head = stack[0]
                    # print("Using head", head)
                    # print("Using stack", stack)
                    # print("Using tokens", tokens)
                    subEffect = subEffectParser(head, stack)
                    if (subEffect) != None:
                        print("Found ", subEffect)
                        if(subEffect['type'] == "Parens"):
                            effects[-1]['limit'] = subEffect
                        else:
                            effects.append(subEffect)   
                        # print("after subeffect stack: ", stack)
                        # print("after subeffect tokens: ", tokens)
                if (subEffect == None):
                    break
    print("Exiting subeffect of ", tokens)
    return effects


def parseAlternativeCostEffect(head, tokens, stopWord=None):
    if (head not in alternativeCosts):
        return None
    effect = {
        'type': head,
    }
    costEndIndex = tokens.index(")")
    effect['cost'] = tokens[costEndIndex-1]
    # +1 for ':' and ' '
    effect['effects'] = parseSubEffect(tokens[costEndIndex + 2:])
    return effect

def splitEffectIntoDifferentPhases(card, effect):
    effectTokens = re.findall(r'\b\w+\b|[^\w\s]|\n', effect)
    effectStack = []
    for effectToken in effectTokens:
        effectStack.append(effectToken)
        if effectToken == newLineToken:
            card['effectTokens'].append(effectStack.copy())
            effectStack.clear()
    card['effectTokens'].append(effectStack.copy())
