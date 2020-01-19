import discord
import data
import ticket_parser
import emotes
from discord.ext import commands

def add_tickets_as_embed_field(embed, ticket_dict, user):
    for coins, tickets in ticket_dict.items():
        ticket_count = len(tickets)
        name = f'{coins} coins'
        if ticket_count > 1:
            name += f' × {ticket_count} = **{cost}** coins'
        embed.add_field(name=name, value=ticket_parser.format_list(tickets))

def sum_cost(user):
    orders = data.get_ticket_orders(user)
    total_cost = 0
    for coins, tickets in orders.items():
        ticket_count = len(tickets)
        cost = coins * ticket_count
        total_cost += cost
    return total_cost

class Lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.event(self.on_reaction_add)
    
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
        
        for t in new_tickets:
            data.add_ticket_order(user, coins, t)
        
        print(data.cache)

        await self.send_ticket_orders_embed(context, user)

    @commands.command(aliases=['o'], brief='Show your ticket orders')
    async def orders(self, context):
        user = context.author
        await self.send_ticket_orders_embed(context, user)

    async def send_ticket_orders_embed(self, context, user):
        embed = self.get_ticket_orders_embed(user)
        message = await context.send(embed=embed)

        if embed.color != discord.Color.orange():
            await message.add_reaction(emotes.MONEY_WINGS)
        await message.add_reaction(emotes.X)

    def get_ticket_orders_embed(self, user):
        economy = self.bot.get_cog('Economy')
        balance = economy.get_coins(user)
        total_cost = sum_cost(user)
        affordable = total_cost and balance >= total_cost

        color = discord.Color.green() if affordable else discord.Color.orange()
        title = f'{user.name}\'s Ticket Orders'
        description = ''
        if not total_cost:
            description = 'No Tickets Ordered'
        elif not affordable:
            description = 'Cannot Afford! **Undo** or **Clear** Orders!'

        balance_after = balance - total_cost
        balance_status = f'Current: **{balance}** coins\n'
        if total_cost:
            balance_status += (
                f'Cost: **{total_cost}** coins\n'
                f'After: **{balance_after}** coins'
            )

        embed = discord.Embed(title=title, color=color, description=description)
        embed.set_footer(text=user.name, icon_url=user.avatar_url)

        ticket_orders = data.get_ticket_orders(user)
        if ticket_orders:
            add_tickets_as_embed_field(embed, ticket_orders, user)

        embed.add_field(name='Balance Status', value=balance_status)
        
        if affordable:
            embed.add_field(name=f'{emotes.MONEY_WINGS} Buy', value='Pay for all of your orders')

        x_desc = 'Clear all your orders' if ticket_orders else 'Close this message'
        embed.add_field(name=f'{emotes.X} Clear', value=x_desc)

        return embed

    def should_ignore_reaction(self, reaction, user):
        message = reaction.message

        reaction_by_bot = user == self.bot.user
        bot_message = message.author == self.bot.user
        has_embeds = message.embeds
        message_for_this_user = has_embeds or user.name not in message.embeds[0].title

        ignored = any([reaction_by_bot, not bot_message, not has_embeds, not message_for_this_user])

        return ignored

    async def on_reaction_add(self, reaction, user):
        if self.should_ignore_reaction(reaction, user):
            return

        message = reaction.message
        embed = message.embeds[0]

        if str(reaction) == emotes.X:
            ticket_orders = data.get_ticket_orders(user)
            if ticket_orders:
                data.clear_ticket_orders(user)
                embed = self.get_ticket_orders_embed(user)
                await message.edit(embed=embed)
            else:
                await message.delete()
        elif str(reaction) == emotes.MONEY_WINGS:
            await self.buy_orders(user)
            await self.send_paid_tickets_embed(message, user)
    
    async def buy_orders(self, user):
        total_cost = sum_cost(user)
        economy = self.bot.get_cog('Economy')
        economy.add_coins(user, -total_cost)
        
        data.transfer_orders_to_paid(user)
        data.clear_ticket_orders(user)

    async def send_paid_tickets_embed(self, message, user):
        embed = self.get_paid_tickets_embed(user)
        new_message = await message.channel.send(embed=embed)
        await message.delete()
        await new_message.add_reaction(emotes.X)
    
    def get_paid_tickets_embed(self, user):
        economy = self.bot.get_cog('Economy')
        balance = economy.get_coins(user)

        title = f'{user.name}\'s Paid Tickets'
        embed = discord.Embed(title=title, color=discord.Color.green())
        embed.set_footer(text=user.name, icon_url=user.avatar_url)

        paid_tickets = data.get_paid_tickets(user)
        add_tickets_as_embed_field(embed, paid_tickets, user)

        embed.add_field(name='Current Balance', value=f'**{balance}** coins')
        embed.add_field(name=f'{emotes.X} Close', value='Close this message')

        return embed

def add_to(bot):
    bot.add_cog(Lottery(bot))