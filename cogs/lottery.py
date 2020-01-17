import discord
import data
import ticket_parser
import emotes
from discord.ext import commands

class Lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def add_order(self, user, coins, ticket_number):
        if user.id not in data.cache:
            data.cache[user.id] = { data.ORDERS: {} }

        orders = data.cache[user.id][data.ORDERS]

        if coins in orders and ticket_number in orders[coins]:
            coins *= 2

        if coins not in orders:
            orders[coins] = []
        
        orders[coins].append(ticket_number)

    def clear_order(self, user):
        data.cache[user.id][data.ORDERS] = {}

    @commands.command(aliases=['b'], brief='Buy tickets for this cycle')
    async def buy(self, context, coins:int, *tickets):
        user = context.author
        try:
            new_tickets = ticket_parser.parse_list(tickets)
        except ValueError as e:
            response = f'{user.mention}\n'
            response += '\n'.join(e.args)
            await context.send(response)
            return
        
        tickets_str = ticket_parser.format_list(new_tickets)
        ticket_count = len(new_tickets)
        
        economy = self.bot.get_cog('Economy')
        balance = economy.get_coins(user)
        
        for t in new_tickets:
            self.add_order(user, coins, t)
        
        print(data.cache)

        embed = discord.Embed(title=f'{user.name}\'s Ticket Order', colour=discord.Color.green())

        total_cost = 0
        orders = data.cache[user.id][data.ORDERS]
        for coins, tickets in orders.items():
            ticket_count = len(tickets)
            cost = coins * ticket_count
            total_cost += cost
            name = f'{coins} coins'
            if ticket_count > 1:
                name += f' × {ticket_count} = **{cost}** coins'
            embed.add_field(name=name, value=ticket_parser.format_list(tickets))

        balance_after = balance - total_cost

        balance_status = (
            f'Current: **{balance}** coins\n'
            f'Cost: **{total_cost}** coins\n'
            f'After: **{balance_after}** coins'
        )
        embed.add_field(name='Balance Status', value=balance_status)
        embed.add_field(name=':x: Clear', value='Clear all your orders')

        embed.set_footer(text=user.name, icon_url=user.avatar_url)

        message = await context.send(embed=embed)

        await message.add_reaction(emotes.X)

def add_to(bot):
    cog = Lottery(bot)
    bot.add_cog(cog)
    return cog