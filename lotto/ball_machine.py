import random
import lotto

from datetime import datetime
from lotto.lottery_result import LotteryResult

def draw():
    random.seed(datetime.now())
    pool = list(range(100))
    winning_balls = random.sample(pool, lotto.TOTAL_BALLS)
    return LotteryResult(winning_balls)