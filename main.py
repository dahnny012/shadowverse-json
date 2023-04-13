import json
import os
from data import getCardPoolFromShadowversePortal
from parsers import *

rotationCardPool = getCardPoolFromShadowversePortal()


def dumpTokenPool():
    for card in tokenPool.values():
        with open(f'{os.getcwd()}/output/tokens/{card["name_"]}.json', 'w') as w:
            w.write(json.dumps(card, indent=4))
            
for card in rotationCardPool:
    baseParser(card)
    with open(f'{os.getcwd()}/output/{card["name_"]}.json', 'w') as w:
        w.write(json.dumps(card, indent=4))
dumpTokenPool()
