import discord
import data
import colors
from discord.ext import commands

DEFAULT_INCOME = 10

INCOME_BRIEF = 'Get 10 coins if you start with no coins'
BALANCE_BRIEF = 'Check your balance'

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['bal'], brief=BALANCE_BRIEF)
    async def balance(self, context):
        user = context.author
        embed = self.get_balance_embed(user)
        if data.get_player(user).balance < DEFAULT_INCOME:
            embed.description += f'\nUse `lott income` to earn up to **{DEFAULT_INCOME}** coins'
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

        low_coins = player.balance < DEFAULT_INCOME
        tickets_bought = player.paid_tickets

        if low_coins and not tickets_bought:
            player.add_to_balance(DEFAULT_INCOME - player.balance)
            embed = self.get_balance_embed(user)
            embed.title = "Here's some coins!"
            await self.bot.get_cog('Lottery').update_ticket_order_embeds(user)
        else:
            embed = self.get_balance_embed(user)
            if low_coins and tickets_bought:
                embed.title = 'Wait until after the result is drawn!'
            else:
                embed.title = "Come back when you're broke!"
        await context.send(embed=embed)


def add_to(bot):
    bot.add_cog(Economy(bot))