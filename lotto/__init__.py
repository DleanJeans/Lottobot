DRAW_SEQUENCE = list(range(7))
DRAW_SEQUENCE[0] = 1
TOTAL_BALLS = sum(DRAW_SEQUENCE)

MULTIPLIERS = [100, 40, 20, 10, 5, 2, 1]
NAMES = ['Sp', '1st', '2nd', '3rd', '4th', '5th', '6th']
PRIZES = list(zip(NAMES, MULTIPLIERS))

INCOME = 10
INCOME_TIP = f'Use `lott income` to earn up to **{INCOME}** coins'

def get_prize_name(prize):
    name, multi = prize
    return f'{name} (×{multi:02})'