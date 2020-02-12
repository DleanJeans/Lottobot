import discord
import inspect
from random import choice

color_factories = inspect.getmembers(discord.Color, predicate=inspect.ismethod)
color_factories = [(name, method) for name, method in color_factories if 'from' not in name]

all_colors = [method for _, method in color_factories]
brights = [method for name, method in color_factories if 'dark' not in name and 'light' not in name]

def random(exceptions=None):
    if type(exceptions) is not list:
        exceptions = [exceptions]
    while True:
        new_color = choice(brights)()
        if new_color not in exceptions:
            return new_color