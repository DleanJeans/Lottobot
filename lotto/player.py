import lotto
from lotto import level

class TicketOrder:
    def __init__(self, coins, tickets):
        self.coins = coins
        self.tickets = tickets
        self.message = None
    
    def total_cost(self):
        return self.coins * len(self.tickets)

class Player:
    def __init__(self, id, balance=0, xp=0):
        self.id = id
        self.balance = balance
        self.xp = xp
        self.reset()
        self.clear_level_up()

    def reset(self):
        self.ticket_orders = []
        self.paid_tickets = {}
        self.total_winnings = 0
    
    def clear_level_up(self):
        self.level_up = ()
    
    def get_income(self):
        return self.get_level() * 10

    def _add_xp(self, xp):
        old_level = self.get_level()
        self.xp += xp
        new_level = self.get_level()

        if new_level > old_level:
            self.level_up = (old_level, new_level)

    def get_level(self):
        return level.xp_to_level(self.xp)
    
    def get_max_tickets(self):
        lvl = self.get_level()
        return lotto.get_max_tickets_for(lvl)
    
    def can_hold_more_tickets(self, order):
        tickets_after_buying = set(list(self.paid_tickets.keys()) + order.tickets)
        return len(tickets_after_buying) <= self.get_max_tickets()

    def can_afford(self, order):
        return self.balance >= order.total_cost()

    def can_buy(self, order):
        return self.can_afford(order) and self.can_hold_more_tickets(order)

    def get_saved_data(self):
        net_worth = self.balance + self.get_total_spendings()
        return { 'balance': net_worth, 'xp': self.xp }

    def get_net_worth(self):
        return self.balance + self.get_total_spendings()

    def has_joined(self):
        return self.ticket_orders or self.paid_tickets

    def pay_prize(self, coins):
        self.add_to_balance(coins)
        self.total_winnings += coins

    def add_to_balance(self, coins):
        self.balance += coins
    
    def add_ticket_order(self, coins, tickets):
        ticket_order = TicketOrder(coins, tickets)
        self.ticket_orders.append(ticket_order)
        return ticket_order
    
    def remove_order(self, message):
        order = self.find_order_by_message(message)
        if order:
            self.ticket_orders.remove(order)

    def find_order_by_message(self, message):
        for order in self.ticket_orders:
            if order.message.id == message.id:
                return order

    def clear_ticket_orders(self):
        self.ticket_orders.clear()
    
    def get_total_spendings(self):
        total = 0
        for ticket, worth in self.paid_tickets.items():
            total += worth
        return total

    def buy_ticket_order(self, order):
        self.balance -= order.total_cost()
        for ticket in order.tickets:
            self.paid_tickets[ticket] = self.paid_tickets.get(ticket, 0) + order.coins

    def group_paid_tickets(self):
        tickets_by_price = {}
        for ticket, price in self.paid_tickets.items():
            if price not in tickets_by_price:
                tickets_by_price[price] = []
            tickets_by_price[price].append(ticket)
        return tickets_by_price
    
    def check_ticket(self, number):
        return self.paid_tickets.get(number, 0)

    def clear_paid_tickets(self):
        self.paid_tickets.clear()