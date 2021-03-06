import json
import time
import discord
from functools import partial
from lotto.player import Player
from discord.ext import tasks

JSON_FILE = 'disk.json'

def load_from_disk():
    with open(JSON_FILE, 'r') as f:
        content = f.read()
        f.seek(0)
        players_data = json.load(f) if content else {}
        
        for id, data in players_data.items():
            id = int(id)
            player = Player(id)

            for key, value in data.items():
                setattr(player, key, value)
            
            players[id] = player

players = {}
disk = {}
load_from_disk()

def clear_players_tickets():
    for p in players.values():
        p.reset()

def get_joined_players(context=None):
    all_players = get_players_in_guild(context.guild) if context else list(players.values())
    joined_players = [p for p in all_players if p.has_joined()]

    return joined_players

def get_players_in_guild(guild=None):
    if not guild:
        return list(players.values())

    users = [mem for mem in guild.members if mem.id in players]
    users = [user for user in users if is_player(user)]
    all_players = [get_player(user) for user in users]
    return all_players

def is_player(user):
    return user.id in players

def get_user(bot, player):
    if type(player) is discord.User: return player
    return bot.get_user(player.id)

def get_player(user):
    if type(user) is Player: return user

    if user.id not in players:
        player = Player(user.id)
        players[user.id] = player
    else:
        player = players[user.id]
    
    return player

def get_balance(user):
    return get_player(user).balance

def add_ticket_order(user, coins, tickets):
    player = get_player(user)
    return player.add_ticket_order(coins, tickets)

@tasks.loop(seconds=5)
async def save_to_disk():
    with open(JSON_FILE, 'w') as f:
        data = {}
        for id, player in players.items():
            player_data = player.get_saved_data()
            if player_data:
                data[id] = player_data
        
        json.dump(data, f)

save_to_disk.start()