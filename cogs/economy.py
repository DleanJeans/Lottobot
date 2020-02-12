import discord
import colors
import lotto
import cogs

from lotto import data, level, embeds, as_coins
from discord.ext import commands

INCOME_BRIEF = f'Get some coins based on your level if you start with less than that'
BALANCE_BRIEF = 'Check your balance'
RICH_BRIEF = 'Show Top 10 richest players in the server'

HERES_SOME_COINS = "Here's some coins!"
WAIT_FOR_RESULT = 'Wait until after the result is drawn!'
COME_BACK = "Come back when you're broke!"

SERVER_RICHEST_PLAYERS = 'Richest players in the server'

MIN_RICH = 1000
EMPTY_RICH = f'At least {as_coins(MIN_RICH)} to show up here.\nGrab your friends and play!'

RICH_PER_PAGE = 10

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['bal'], brief=BALANCE_BRIEF)
    async def balance(self, context):
        user = context.author
        player = data.get_player(user)
        income = player.get_income()

        embed = self.get_balance_embed(user)
        if player.balance < income:
            embed.description += '\n' + lotto.INCOME_TIP + as_coins(income)
        await context.send(embed=embed)

    def get_balance_embed(self, user):
        coins = data.get_balance(user)
        description='**Coins**: `{:,}`'.format(coins).replace(',', ' ')

        embed = embeds.create(footer_user=user, description=description)
        return embed

    @commands.command(aliases=['in'], brief=INCOME_BRIEF)
    async def income(self, context):
        user = context.author
        player = data.get_player(user)
        income = player.get_income()

        low_coins = player.balance < income
        tickets_bought = player.paid_tickets

        title = None
        eligible = low_coins and not tickets_bought

        if eligible:
            await self.bot.get_cog(cogs.LEVEL_SYSTEM).add_xp(context, user, level.INCOME_XP)
            if player.level_up:
                income = player.get_income()

            player.add_to_balance(income - player.balance)
            embed = self.get_balance_embed(user)
            title = HERES_SOME_COINS
        else:
            embed = self.get_balance_embed(user)
            if low_coins and tickets_bought:
                title = WAIT_FOR_RESULT
            else:
                title = COME_BACK
            
        embed.set_author(name=title)
        await context.send(embed=embed)
        if eligible:
            await self.bot.get_cog(cogs.LOTTERY).update_ticket_order_embeds(user)
    
    @commands.command(brief=RICH_BRIEF)
    async def rich(self, context):
        if not context.guild: return

        ranks = []
        guild_players = data.get_players_in_guild(context.guild)[:RICH_PER_PAGE]
        guild_players.sort(key=lambda p: p.get_net_worth(), reverse=True)

        for i, player in enumerate(guild_players):
            net_worth = player.get_net_worth()
            if net_worth < MIN_RICH:
                continue
            user = self.bot.get_user(player.id)
            coins = as_coins(net_worth, suffix=False)
            rank = f'#{i+1:2} | {coins}'
            if user:
                rank += f' - {user.mention}'
            ranks.append(rank)
        
        embed = embeds.create()
        embed.set_author(name=SERVER_RICHEST_PLAYERS)
        embed.description = '\n'.join(ranks)
        
        if len(ranks) < RICH_PER_PAGE:
            embed.description += '\n' + EMPTY_RICH

        await context.send(embed=embed)

def add_to(bot):
    bot.add_cog(Economy(bot))