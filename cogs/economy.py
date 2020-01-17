import discord
import data
from discord.ext import commands

INCOME_BRIEF = 'Get 10 coins once if you start with no coins'
BALANCE_BRIEF = 'Check your balance'

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.default_income = 10

    def add_coins(self, user, coins):
        new_balance = self.get_coins(user) + coins
        data.set_value(user, data.COINS, new_balance)
    
    def get_coins(self, user):
        return data.get_value(user, data.COINS, 0)

    @commands.command(aliases=['bal'], brief=BALANCE_BRIEF)
    async def balance(self, context):
        coins = self.get_coins(context.author)
        response = f'{context.author.mention} You have **{coins}** coins'
        await context.send(response)

    @commands.command(aliases=['in'], brief=INCOME_BRIEF)
    async def income(self, context):
        no_coins = self.get_coins(context.author) == 0
        no_tickets_bought = True

        if no_coins and no_tickets_bought:
            self.add_coins(context.author, self.default_income)

            response = f'{context.author.mention} has received **{self.default_income}** coins!'
            await context.send(response)
        else:
            await context.send('Come back when you\'re broke!')


def add_to(bot):
    bot.add_cog(Economy(bot))