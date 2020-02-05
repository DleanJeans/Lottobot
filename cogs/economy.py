import discord
import data
from discord.ext import commands

INCOME_BRIEF = 'Get 10 coins if you start with no coins'
BALANCE_BRIEF = 'Check your balance'

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.default_income = 10

    @commands.command(aliases=['bal'], brief=BALANCE_BRIEF)
    async def balance(self, context):
        user = context.author
        embed = self.get_balance_embed(user)
        await context.send(embed=embed)

    def get_balance_embed(self, user):
        coins = data.get_balance(user)
        embed = discord.Embed(description=f'**Coins**: {coins}')
        embed.set_footer(text=user.name, icon_url=user.avatar_url)
        return embed

    @commands.command(aliases=['in'], brief=INCOME_BRIEF)
    async def income(self, context):
        user = context.author
        player = data.get_player(user)

        no_coins = data.get_balance(context.author) == 0
        no_tickets_bought = not player.paid_tickets

        if no_coins and no_tickets_bought:
            player.add_to_balance(self.default_income)
            embed = self.get_balance_embed(user)
            embed.title = "Here's some coins!"
            await context.send(embed=embed)
            await self.bot.get_cog('Lottery').update_ticket_order_embeds(user)
        else:
            await context.send("Come back when you're broke!")


def add_to(bot):
    bot.add_cog(Economy(bot))