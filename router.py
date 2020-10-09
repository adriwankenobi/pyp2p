#!/usr/bin/env python3
'''
Routing algoritms
'''

def simplerouter(peerid, knownpeers, maxpeers, discarded):
    """ Returns first peer found. Brute force. O(N)"""

    assert len(knownpeers) + 1 <= maxpeers
    if peerid in knownpeers and peerid not in discarded:
        return peerid, knownpeers[peerid][0], knownpeers[peerid][1]

    for p in knownpeers:
        if p not in discarded:
            return p, knownpeers[p][0], knownpeers[p][1]

    return None, None, None


def distancerouter(peerid, knownpeers, maxpeers, discarded):
    """ Returns peer within less distance to the target peer. O(N/2)"""

    assert len(knownpeers) + 1 <= maxpeers
    if peerid in knownpeers and peerid not in discarded:
        return peerid, knownpeers[peerid][0], knownpeers[peerid][1]

    # If peer is not known, get the closest by pid
    # Assuming peer ids in the format 'p00'
    target = int(peerid[1:])

    selected = None
    distance = maxpeers+1
    for p in knownpeers:
        if p not in discarded:
            pd = abs(target-int(p[1:]))
            if pd < distance:
                selected = p
                distance = pd

    if selected is None:
        return None, None, None

    return selected, knownpeers[selected][0], knownpeers[selected][1]