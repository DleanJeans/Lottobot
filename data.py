import json
import time
from functools import partial
from player import Player
from discord.ext import tasks

JSON_FILE = 'disk.json'
COINS = 'coins'
PAID_TICKETS = 'paid_tickets'
TICKET_ORDERS = 'ticket_orders'

players = {}

def load_from_disk():
    with open(JSON_FILE, 'r') as f:
        content = f.read()
        f.seek(0)
        players_data = json.load(f) if content else {}
        
        for id, data in players_data.items():
            id = int(id)
            player = Player()

            for key, value in data.items():
                setattr(player, key, value)
            
            players[id] = player

load_from_disk()

disk = {}

def get_player(user):
    if user.id not in players:
        player = Player()
        players[user.id] = player
    else:
        player = players[user.id]
    
    return player

def get_balance(user):
    return get_player(user).balance

def add_ticket_order(user, coins, tickets):
    player = get_player(user)
    return player.add_ticket_order(coins, tickets)

@tasks.loop(seconds=10)
async def save_to_disk():
    with open(JSON_FILE, 'w') as f:
        data = {}
        for id, player in players.items():
            data[id] = player.get_saved_data()
        
        json.dump(data, f)

save_to_disk.start()