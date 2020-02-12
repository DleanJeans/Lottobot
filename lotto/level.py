from math import sqrt, log10

INCOME_XP = 1
BUY_XP = 2
PRIZES_XP = [50, 30, 25, 20, 15, 10, 5]


def fib(n):
    return int(((1+sqrt(5))**n-(1-sqrt(5))**n)/(2**n*sqrt(5)))

def gap(lvl):
    value = fib(lvl+1)
    round_to = 1
    if value >= 100:
        round_to = 10 ** int(log10(value)-1)
    elif value >= 5:
        round_to = 5
    
    value = round(value / round_to) * round_to
    
    return value * 10

def xp_for_level(lvl):
    xp = sum([gap(i) for i in range(lvl, 0, -1)])
    return xp

def xp_to_level(xp):
    lvl = 1
    while True:
        xp_cap = xp_for_level(lvl)
        if xp < xp_cap:
            return lvl
        lvl += 1