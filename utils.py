# -*- coding: utf-8 -*-

from collections import deque

from pysodium import randombytes


def toposort(nodes, parents):
    seen = {}

    def visit(u):
        if u in seen:
            if seen[u] == 0:
                raise ValueError('not a DAG')
        elif u in nodes:
            seen[u] = 0
            for v in parents(u):
                yield from visit(v)
            seen[u] = 1
            yield u

    for u in nodes:
        yield from visit(u)


def bfs(s, succ):
    s = tuple(s)
    seen = set(s)
    q = deque(s)
    while q:
        u = q.popleft()
        yield u
        for v in succ(u):
            if not v in seen:
                seen.add(v)
                q.append(v)


def dfs(s, succ):
    seen = set()
    q = [s]
    while q:
        u = q.pop()
        yield u
        seen.add(u)
        for v in succ(u):
            if v not in seen:
                q.append(v)


def randrange(n):
    a = (n.bit_length() + 7) // 8  # number of bytes to store n
    b = 8 * a - n.bit_length()  # number of shifts to have good bit number
    r = int.from_bytes(randombytes(a), byteorder='big') >> b
    while r >= n:
        r = int.from_bytes(randombytes(a), byteorder='big') >> b
    return r


def _sortest_(h, height, reverse):
    s = sorted(h, key=lambda u: height(u), reverse=reverse)
    m = height(s[0])
    g = []
    for i in range(len(s)):
        if height(s[i]) == m:
            g.append(s[i])
        else:
            break
    return g


def highest(h, height):
    return _sortest_(h, height, reverse=True)


def lowest(h, height):
    return _sortest_(h, height, reverse=False)


def _diffsort_(c, h, height, can_see, reverse):
    g = {}
    e = can_see(c)
    for (k, v) in h.items():
        if v == c:
            continue
        a = height(v)
        b = height(e[k]) if k in e else 0
        g[v] = a - b
    return _sortest_(g.keys(), lambda u: g[u], reverse)


def more_diff(c, h, height, can_see):
    return _diffsort_(c, h, height, can_see, reverse=True)


def less_diff(c, h, height, can_see):
    return _diffsort_(c, h, height, can_see, reverse=False)
