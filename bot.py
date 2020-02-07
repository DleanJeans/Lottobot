import os
import discord

from discord.ext.commands import Bot
from dotenv import load_dotenv
from cogs import economy, lottery

bot = Bot(command_prefix=['lott ', 'lot ', 'lo '])
economy.add_to(bot)
lottery.add_to(bot)

@bot.event
async def on_ready():
    status = 'lott help'
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(status))
    print('Logged in as', bot.user.name, f'(#{bot.user.discriminator})')

PLUS = False
env_name = 'PLUS_TOKEN' if PLUS else 'BOT_TOKEN'

load_dotenv()
TOKEN = os.getenv(env_name)
bot.run(TOKEN)