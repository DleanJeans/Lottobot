import random
from datetime import datetime
from lotto.draw_result import DrawResult

DRAW_SEQUENCE = list(range(7))
DRAW_SEQUENCE[0] = 1
TOTAL_BALLS = sum(DRAW_SEQUENCE)

def draw():
    random.seed(datetime.now())
    pool = list(range(100))
    winning_balls = random.sample(pool, TOTAL_BALLS)
    return DrawResult(winning_balls)