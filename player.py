class TicketOrder:
    def __init__(self, coins, tickets):
        self.coins = coins
        self.tickets = tickets
        self.message = None
    
    def total_cost(self):
        return self.coins * len(self.tickets)

class Player:
    def __init__(self, balance=0):
        self.balance = balance
        self.ticket_orders = []
        self.paid_tickets = {}
    
    def get_saved_data(self):
        return { 'balance': self.balance }
    
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

    def clear_paid_tickets(self):
        self.paid_tickets.clear()