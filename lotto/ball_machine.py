import random
import lotto

from datetime import datetime
from lotto.draw_result import DrawResult

def draw():
    random.seed(datetime.now())
    pool = list(range(100))
    winning_balls = random.sample(pool, lotto.TOTAL_BALLS)
    return DrawResult(winning_balls)