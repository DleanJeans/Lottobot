DRAW_SEQUENCE = list(range(7))
DRAW_SEQUENCE[0] = 1
TOTAL_BALLS = sum(DRAW_SEQUENCE)

MULTIPLIERS = [100, 40, 20, 10, 5, 2, 1]
NAMES = ['Sp', '1st', '2nd', '3rd', '4th', '5th', '6th']
PRIZES = list(zip(NAMES, MULTIPLIERS))

INCOME_TIP = 'Use `lott income` to earn up to '

CYCLE_INTERVAL = 2

def get_prize_name(prize):
    name, multi = prize
    return f'{name} (×{multi:02})'

def as_coins(coins, bold=True, suffix=True, backtick=False):
    bold = not backtick
    output = '{:,}'.format(coins).replace(',', ' ')
    if bold: output = f'**{output}**'
    if backtick: output = f'`{output}`'
    if suffix: output += ' coins'
    return output

def get_max_tickets_for(level):
    levels = [15, 10, 5]
    maxes = [5, 4, 3]

    for lvl, m in zip(levels, maxes):
        if level >= lvl:
            return m
    return 2