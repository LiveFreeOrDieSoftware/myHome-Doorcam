from collections import namedtuple

Card = namedtuple("Card", "name proba proba0 rect img time")


def cardsOverlap(cardA, cardB, lim=1000):
    return intersect(cardA.rect, cardB.rect) > lim


def intersect(a, b):
    """ returns 0 if rectangles don't intersect
    each rect: (startX, startY, endX, endY)
    https://stackoverflow.com/a/27162334
    """
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    if (dx >= 0) and (dy >= 0):
        return dx*dy
    return 0
