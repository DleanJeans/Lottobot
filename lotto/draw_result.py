import lotto

format_ball = lambda b: '{:02}'.format(b) if b >= 0 else '  '
CENTER_LENGTH = 24
HIDDEN = -1

def divide_balls(balls):
    balls = list(balls)
    tiered = []
    for tier_count in lotto.DRAW_SEQUENCE[::-1]:
        balls_in_tier = balls[:tier_count]
        missing = tier_count - len(balls_in_tier)
        if missing:
            balls_in_tier += missing * [HIDDEN]
        tiered.append(balls_in_tier)
        balls = balls[tier_count:]
    tiered.reverse()
    return tiered

class DrawResult:
    def __init__(self, balls):
        self.balls = balls
        self.revealed_balls = []
        self.displayed_balls = []
        self.revealed = 0
        self.last_revealed = None
    
    def revealed_all(self):
        return self.revealed >= lotto.TOTAL_BALLS

    def get_number_prize_name(self, number):
        for i, tier in enumerate(self.displayed_balls):
            if number in tier:
                prize = lotto.PRIZES[i]
                return lotto.get_prize_name(prize)

    def reveal(self):
        self.revealed = min(self.revealed + 1, lotto.TOTAL_BALLS)
        self.revealed_balls = self.balls[:self.revealed]
        self.displayed_balls = divide_balls(self.revealed_balls)
        self.last_revealed = self.revealed_balls[-1]
        self.last_prize = self.get_ticket_prize(self.last_revealed)

        return str(self)

    def __str__(self):
        output = []

        for balls, prize in zip(self.displayed_balls, lotto.PRIZES):
            balls = map(format_ball, balls)
            balls = '  '.join(balls).center(CENTER_LENGTH)
            prize_name = lotto.get_prize_name(prize)
            output += [f'{prize_name} |{balls}']
        
        output = '\n'.join(output)
        return output
    
    def get_ticket_prize(self, number):
        for balls, prize in zip(self.displayed_balls, lotto.PRIZES):
            if number in balls:
                return prize

    def compare_tickets(self, player):
        winning_tickets = []
        for balls, prize in zip(self.displayed_balls, lotto.PRIZES):
            winning_in_tier = []
            for ticket, worth in player.paid_tickets.items():
                if ticket in balls:
                    winning_in_tier.append((ticket, worth))  
            winning_tickets.append(winning_in_tier)
        return winning_tickets