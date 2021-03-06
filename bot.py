import os
import discord

from discord.ext.commands import Bot
from dotenv import load_dotenv
from cogs import economy, lottery, level_system

load_dotenv()
TESTING = os.getenv('TESTING')
TESTING = int(TESTING)

prefixes = ['lott ', 'lot ', 'lo '] if not TESTING else ['+']
for p in list(prefixes):
    prefixes.append(p.capitalize())
    prefixes.append(p.strip())

bot = Bot(command_prefix=prefixes)
economy.add_to(bot)
lottery.add_to(bot)
level_system.add_to(bot)

@bot.event
async def on_ready():
    status = 'lott help'
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(status))
    print('Logged in as', bot.user.name, f'(#{bot.user.discriminator})')

env_name = 'TESTING_TOKEN' if TESTING else 'BOT_TOKEN'

TOKEN = os.getenv(env_name)
bot.run(TOKEN)