import os
import discord
import emotes

from discord.ext.commands import Bot
from dotenv import load_dotenv
import cogs.economy, cogs.lottery

bot = Bot(command_prefix=['lo ', 'lott '])
cogs.economy.add_to(bot)
lottery = cogs.lottery.add_to(bot)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('lott help'))
    print('Logged in as', bot.user)

@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user: return
    if str(reaction) == emotes.X:
        message = reaction.message
        if message.author != bot.user:
            return
        if message.embeds:
            embed = message.embeds[0]
            if user.name in embed.title:
                lottery.clear_order(user)
                await message.delete()

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
bot.run(TOKEN)