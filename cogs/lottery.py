import asyncio
import discord
import pytz

import data
import emotes
import embeds
import colors
import ticket_parser

from datetime import datetime
from lotto import ball_machine
from discord.ext import commands

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
        
        order = data.add_ticket_order(user, coins, new_tickets)
        
        await self.send_ticket_order_embed(context, user, order)

    async def send_ticket_order_embed(self, context, user, order):
        embed = embeds.embed_ticket_order(user, order)

        message = await context.send(embed=embed)
        order.message = message

        if embed.color == embeds.AFFORDABLE_COLOR:
            await message.add_reaction(emotes.MONEY_WINGS)
        await message.add_reaction(emotes.X)

    @commands.command(aliases=['t'], brief='Show all your paid ticket numbers')
    async def tickets(self, context):
        user = context.author
        player = data.get_player(user)
        if player.paid_tickets:
            embed = embeds.embed_paid_tickets(user)
            message = await message.send(embed=embed)
            await message.add_reaction(emotes.X)
        else:
            await context.send(f"{user.mention} You haven't bought any tickets yet!")

    @commands.command(aliases=['o'], brief='Show all your ticket orders')
    async def orders(self, context):
        user = context.author
        player = data.get_player(user)

        for order in player.ticket_orders:
            await self.send_ticket_order_embed(context, user, order)
        
        if not player.ticket_orders:
            await context.send(f'{user.mention} You have no ticket orders!')

    @commands.command()
    async def draw(self, context):
        result = ball_machine.draw()
        embed = discord.Embed(title='Draw Result')
        embed.timestamp = datetime.now().astimezone()
        
        message = None
        while not result.revealed_all():
            embed.color = colors.random_bright(embed.color)
            embed.description = '```%s```' % result.reveal()
            if result.last_revealed:
                prize_name = result.get_number_prize_name(result.last_revealed)
                embed.description = f'`{prize_name}:` **{result.last_revealed}**\n' + embed.description

            if not message:
                message = await context.send(embed=embed)
            else:
                await message.edit(embed=embed)
            await asyncio.sleep(1)
        
        embed.description = '```%s```' % result.reveal()
        await message.edit(embed=embed)

    async def on_reaction_add(self, reaction, user):
        if self.should_ignore_reaction(reaction, user):
            return

        message = reaction.message
        embed = message.embeds[0]
        player = data.get_player(user)

        if str(reaction) == emotes.X:
            player.remove_order(message)
            await message.delete()
        
        elif str(reaction) == emotes.MONEY_WINGS:
            order = player.find_order_by_message(message)
            if order:
                player.buy_ticket_order(order)
                player.remove_order(message)

                embed = embeds.embed_paid_tickets(user)
                await message.edit(embed=embed)
                await message.remove_reaction(emotes.MONEY_WINGS, self.bot.user)
                await self.update_ticket_order_embeds(user)

    def should_ignore_reaction(self, reaction, user):
        message = reaction.message

        reaction_by_bot = user == self.bot.user
        bot_message = message.author == self.bot.user
        has_embeds = message.embeds
        message_for_this_user = has_embeds and user.name in message.embeds[0].title

        ignored = any([reaction_by_bot, not bot_message, not has_embeds, not message_for_this_user])

        return ignored

    async def update_ticket_order_embeds(self, user):
        player = data.get_player(user)
        for order in player.ticket_orders:
            message = order.message
            if not message: continue

            new_embed = embeds.embed_ticket_order(user, order)
            await message.edit(embed=new_embed)
            if emotes.MONEY_WINGS not in message.reactions:
                await message.remove_reaction(emotes.X, self.bot.user)
                await message.add_reaction(emotes.MONEY_WINGS)
                await message.add_reaction(emotes.X)

def add_to(bot):
    bot.add_cog(Lottery(bot))