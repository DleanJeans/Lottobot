import discord
import colors
import lotto

from lotto import data, as_coins
from discord.ext import commands

INCOME_BRIEF = f'Get {lotto.INCOME} coins if you start with less than that'
BALANCE_BRIEF = 'Check your balance'
RICH_BRIEF = 'Show Top 10 richest players in the server'

HERES_SOME_COINS = "Here's some coins!"
WAIT_FOR_RESULT = 'Wait until after the result is drawn!'
COME_BACK = "Come back when you're broke!"

RICH_PER_PAGE = 10

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['bal'], brief=BALANCE_BRIEF)
    async def balance(self, context):
        user = context.author
        embed = self.get_balance_embed(user)
        if data.get_player(user).balance < lotto.INCOME:
            embed.description += '\n' + lotto.INCOME_TIP
        await context.send(embed=embed)

    def get_balance_embed(self, user):
        coins = data.get_balance(user)
        embed = discord.Embed(description='**Coins**: {:,}'.format(coins).replace(',', ' '))
        embed.set_footer(text=user.name, icon_url=user.avatar_url)
        embed.color = colors.random_bright()
        return embed

    @commands.command(aliases=['in'], brief=INCOME_BRIEF)
    async def income(self, context):
        user = context.author
        player = data.get_player(user)

        low_coins = player.balance < lotto.INCOME
        tickets_bought = player.paid_tickets

        if low_coins and not tickets_bought:
            player.add_to_balance(lotto.INCOME - player.balance)
            embed = self.get_balance_embed(user)
            embed.title = HERES_SOME_COINS
            await self.bot.get_cog('Lottery').update_ticket_order_embeds(user)
        else:
            embed = self.get_balance_embed(user)
            if low_coins and tickets_bought:
                embed.title = WAIT_FOR_RESULT
            else:
                embed.title = COME_BACK
        await context.send(embed=embed)
    
    @commands.command(brief=RICH_BRIEF)
    async def rich(self, context):
        if not context.guild: return

        ranks = []
        guild_players = data.get_players_in_guild(context.guild)[:RICH_PER_PAGE]
        guild_players.sort(key=lambda p: p.get_net_worth(), reverse=True)

        for i, player in enumerate(guild_players):
            net_worth = player.get_net_worth()
            if net_worth < lotto.INCOME ** 2:
                continue
            user = self.bot.get_user(player.id)
            coins = as_coins(net_worth, suffix=False)
            rank = f'#{i+1:2} | {coins}'
            if user:
                rank += f' - {user.mention}'
            ranks.append(rank)
        
        embed = discord.Embed()
        embed.color = colors.random_bright()
        embed.set_author(name='Richest players in the server')
        embed.description = '\n'.join(ranks)

        await context.send(embed=embed)

def add_to(bot):
    bot.add_cog(Economy(bot))