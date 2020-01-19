import json
import time
from functools import partial
from threading import Thread

JSON_FILE = 'disk.json'
COINS = 'coins'
PAID_TICKETS = 'paid_tickets'
TICKET_ORDERS = 'ticket_orders'

def load_from_disk():
        with open(JSON_FILE, 'r') as f:
            return json.load(f)

disk = load_from_disk()
cache = {}

def get_user_dict(input_dict, user):
    user_id = str(user.id)
    if user_id not in input_dict:
        input_dict[user_id] = {}
    return input_dict[user_id]

def get_dict(input_dict, user, key, default=None):
    user_dict = get_user_dict(input_dict, user)
    if key not in user_dict:
        user_dict[key] = default
    return user_dict[key]

def set_dict(input_dict, user, key, value):
    user_dict = get_user_dict(input_dict, user)
    user_dict[key] = value

get_disk = partial(get_dict, disk)
set_disk = partial(set_dict, disk)
get_cache = partial(get_dict, cache)
set_cache = partial(set_dict, cache)

def get_ticket_orders(user):
    return get_cache(user, TICKET_ORDERS, {})

def get_paid_tickets(user):
    return get_cache(user, PAID_TICKETS, {})

def add_ticket_order(user, coins, ticket_number):
    ticket_orders = get_ticket_orders(user)
    print(ticket_orders)
    add_ticket_to(ticket_orders, coins, ticket_number)

def add_paid_ticket(user, coins, ticket_number):
    paid_tickets = get_paid_tickets(user)
    add_ticket_to(paid_tickets, coins, ticket_number)

def transfer_orders_to_paid(user):
    ticket_orders = get_ticket_orders(user)
    paid_tickets = get_paid_tickets(user)

    for coins, tickets in ticket_orders.items():
        for t in tickets:
            add_paid_ticket(user, coins, t)

def clear_ticket_orders(user):
    user_id = str(user.id)
    cache[user_id][TICKET_ORDERS] = {}

def clear_paid_tickets(user):
    user_id = str(user.id)
    cache[user_id][PAID_TICKETS] = {}

def add_ticket_to(ticket_dict, coins, ticket_number):
    # ticket with the same price already
    same_ticket_ordered = coins in ticket_dict and ticket_number in ticket_dict[coins]
    if same_ticket_ordered:
        coins *= 2

    no_ticket_with_that_price = coins not in ticket_dict
    if no_ticket_with_that_price:
        ticket_dict[coins] = []
    
    ticket_dict[coins].append(ticket_number)

def save():
    with open(JSON_FILE, 'w') as f:
        json.dump(disk, f)

def save_loop(interval=10):
    while True:
        time.sleep(interval)
        save()

Thread(target=save_loop).start()