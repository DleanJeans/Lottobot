from lotto import ball_machine

MULTIPLIERS = [100, 40, 20, 10, 5, 2, 1]
NAMES = ['Sp', '1st', '2nd', '3rd', '4th', '5th', '6th']
PRIZES = list(zip(NAMES, MULTIPLIERS))

format_ball = lambda s: '{:02}'.format(s) if type(s) is int else s
CENTER_LENGTH = 24

def divide_balls(balls):
    balls = list(balls)
    tiered = []
    for tier_count in ball_machine.DRAW_SEQUENCE[::-1]:
        balls_in_tier = balls[:tier_count]
        missing = tier_count - len(balls_in_tier)
        if missing:
            balls_in_tier += missing * ['  ']
        tiered.append(balls_in_tier)
        balls = balls[tier_count:]
    tiered.reverse()
    return tiered

def get_prize_name(prize):
    name, multi = prize
    return f'{name} (×{multi:02})'

class DrawResult:
    def __init__(self, balls):
        self.balls = balls
        self.revealed_balls = []
        self.displayed_balls = []
        self.revealed = 0
        self.last_revealed = ''
    
    def revealed_all(self):
        return self.revealed >= ball_machine.TOTAL_BALLS

    def get_number_prize_name(self, number):
        for i, tier in enumerate(self.displayed_balls):
            if format_ball(number) in tier:
                prize = PRIZES[i]
                return get_prize_name(prize)

    def reveal(self):
        self.revealed = min(self.revealed + 1, ball_machine.TOTAL_BALLS)
        self.revealed_balls = self.balls[:self.revealed]
        self.revealed_balls = list(map(format_ball, self.revealed_balls))
        self.displayed_balls = divide_balls(self.revealed_balls)
        self.last_revealed = self.revealed_balls[-1] if not self.revealed_all() else ''

        return str(self)

    def __str__(self):
        output = []

        for balls, prize in zip(self.displayed_balls, PRIZES):
            balls = '  '.join(balls).center(CENTER_LENGTH)
            prize_name = get_prize_name(prize)
            output += [f'{prize_name}:{balls}']
        
        output = '\n'.join(output)
        return output