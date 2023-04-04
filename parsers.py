import json
import os
import re
import itertools
from utils import consumeTokens, popArrayAfterSearch, popArrayTill, safeIndex


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
give = "give"
thisMatch = "this match"

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
        thenToken,
        triggerPhaseOfTurnToken,
        parseTriggerEffects,
        changeCard
    ]


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


def parseTriggerEffects(head, tokens):
    if head not in triggerEffects:
        return None
    tokens.pop(0)
    return {
        'type': head,
        'effects': parseIffEffect(tokens)
    }


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


def parseOtherwise(head, tokens):
    if (head != otherwise):
        return None
    popArrayAfterSearch(tokens, ",")
    return {
        'type': otherwise,
        'effects': parseSubEffect(tokens)
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
    print("Entered whenever ", tokens)
    return {
        'type': whenever,
        "effects": parseIffEffect(tokens)
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
    # Fusion:
    consumeTokens(tokens, 2)
    types = popArrayAfterSearch(tokens, "\n")
    print(tokens)
    return {
        'type': fusion,
        'cardTypes': types
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
    if (head != summon and head.capitalize() != summon):
        return None
    tokens.pop(0)
    return {
        "type": summon,
        "effects": parseUnits(tokens)
    }


def putToken(head, tokens):
    if (head != put and head.capitalize() != put):
        return None
    intoStopWord = "into"
    print("Entered Put Token ", tokens)
    tokens.pop(0)
    units = parseUnits(tokens, stopWord=intoStopWord)
    print("Left parse units ", tokens)
    destinationList = popArrayTill(tokens, 2)
    print("Checking where to put units ", units)
    print("DestinationList ", destinationList)
    if (hand in destinationList):
        destination = hand
    if (deck in destinationList):
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
    if (tokens[0] == ","):
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
    conditionEffect = parseCondition(tokens)
    endIndex = safeIndex(tokens, endEffectToken)
    if (endIndex >= 0):
        tokens = popArrayTill(tokens, endIndex)
    print("Parsing if subeffect ", tokens)
    thenEffect = parseSubEffect(tokens)
    return {
        'conditions': conditionEffect,
        'then': thenEffect
    }

def parseCondition(tokens):
    print("Entered conditions with tokens ", tokens)
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
        print("Found OR condition ", conditionTokens)
        consumeTokens(conditionTokens, 1)
        conditions.append(parseCondition(conditionTokens)[0])
    return list(conditions)


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
    if (head != "("):
        return None
    return {
        "type": "Parens",
        "condition": popArrayAfterSearch(tokens, ")")
    }


def parseStatChange(tokens, gainStack):
    print("Entering stat change", tokens)
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
            print("Found Unknown ", tokens)
            gain = {
                'type': 'Unknown',
                'tokens': popArrayAfterSearch(tokens, ".")
            }
            break
    return gainStack

def isANameToken(token):
    partOfName = {","}
    return  token[0].isupper() or  token  in partOfName

def parseUnits(tokens, quantifier=None, stopWord=None):
    print("Starting to parse units , ", tokens)
    units = []
    unitStack = []
    unit = {}
    stop = {andd, stopWord, andList}
    quantifiers = {"an", "a"}
    specifics = {"different", "random"}

    while len(tokens) > 0:
        token = tokens.pop(0)
        if (tokens[0] in quantifiers or token.isnumeric()):
            unit['quantifer'] = token
        elif(isANameToken(token)):
            unitStack.append(token)
            if(token == "Lloyd"):
                unitStack.append(consumeTokens(tokens, 3))
        elif(token in specifics):
            if(token == random):
                unit['random'] = True
            if(token == "different"):
                unit['different'] = True
        elif (token == endEffectToken
              or token in stop
              or not isANameToken(token)
              or len(tokens) == 0):
            if(len(unitStack) > 0):
                print("Unit stack", unitStack)
                unitName = " ".join(unitStack)
                # what is this for
                unit["type"] = SummonUnitOrEffect(unitName)
                if unit["type"] == "Card":
                    unit["cardname"] = unitName
                units.append(unit)
                unitStack = []
                if(token == andd and not tokens[0][0].isupper()):
                    print("Card has a trigger ", tokens)
                    unit['and'] = parseSubEffect(tokens)
                unit = {}
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
                        if (subEffect['type'] == otherwise and effects[-1]['type'] == iff):
                            effects[-1]['effects']['otherwise'] = subEffect
                        elif (subEffect['type'] == "Parens"):
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
    print("Entering subeffect for ", head)
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
