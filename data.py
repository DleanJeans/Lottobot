import json
import time
from threading import Thread

JSON_FILE = 'users.json'
COINS = 'coins'
TICKETS = 'tickets'
ORDERS = 'orders'

def load_users():
        with open(JSON_FILE, 'r') as f:
            return json.load(f)

users = load_users()
cache = {}

def set_value(user, key, value):
    user_id = str(user.id)
    data = users.get(user_id, {})
    data[key] = value
    users[user_id] = data

def get_value(user, key, default=None):
    data = users.get(str(user.id), {})
    return data.get(key, default)

def save():
    with open(JSON_FILE, 'w') as f:
        json.dump(users, f)

def save_loop(interval=10):
    while True:
        time.sleep(interval)
        save()

Thread(target=save_loop).start()