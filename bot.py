import os
import discord

from discord.ext.commands import Bot
from dotenv import load_dotenv
from cogs import economy, lottery

bot = Bot(command_prefix=['lo ', 'lot ', 'lott '])
economy.add_to(bot)
lottery.add_to(bot)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('lott help'))
    print('Logged in as', bot.user)

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
bot.run(TOKEN)