notFound = -1

def find_matches(arr, pattern):
    matches = []
    for i, elem in enumerate(arr):
        if re.search(pattern, elem):
            matches.append((i, elem))
    return matches


def splitListBy(lst, matches):
    sublists = []
    prev_index = 0
    for index, type in matches:
        split = {
            'type': type,
            'list': lst[prev_index:index+1]
        }
        sublists.append(split)
        prev_index = index+1
    return sublists

def popArrayAfterSearch(lst, search):
    index = safeIndex(lst, search)
    if(index >0):
        return popArrayTill(lst, index+1)
    return None

def consumeTokens(tokens, numberOfTokens):
    stack = []
    i = 0
    while i < numberOfTokens:
        stack.append(tokens.pop(0))
        i += 1
    return stack


def popArrayTill(lst, index):
    stack = []
    i = 0
    if len(lst) == 0 or index > len(lst):
        return []
    while i < index:
        stack.append(lst.pop(0))
        i += 1
    return stack


def safeIndex(lst, search, stop="."):
    for i, word in enumerate(lst):
        if search == word:
            return i
        if word == stop:
            return notFound
    return notFound
