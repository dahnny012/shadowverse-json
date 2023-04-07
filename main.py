import json
import os
from data import getCardPoolFromShadowverseJson, getCardPoolFromShadowversePortal
from parsers import *

rotationCardPool = getCardPoolFromShadowversePortal()

for card in rotationCardPool:
    baseParser(card)
    with open(f'{os.getcwd()}/output/{card["name_"]}.json', 'w') as w:
        w.write(json.dumps(card, indent=4))