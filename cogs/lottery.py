import asyncio
import discord
import pytz

import data
import emotes
import embeds
import colors
import ticket_parser

from datetime import datetime
from lotto import ball_machine, draw_result
from discord.ext import commands
from datetime import datetime, timedelta

def ceil_datetime(dt, minutes=1):
    delta = timedelta(minutes=minutes)
    return dt + (datetime.min - dt) % delta

class Lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reset()
    
    def reset(self):
        self.scheduled = False
        self.next_draw = None
        self.orders_blocked = False
        self.guilds_announce_channel = {}
        data.clear_players_tickets()
    
    async def block_orders(self):
        self.orders_blocked = True
        players = data.get_joined_players()
        for p in players:
            user = self.bot.get_user(p.id)
            await self.update_ticket_order_embeds(user)

    @commands.command(aliases=['b'], brief='Buy tickets for this cycle')
    async def buy(self, context, coins:int, *tickets):
        user = context.author
        if self.orders_blocked:
            response = f'{user.name}\nHold on a minute! The result is being announced right now!'
            await context.send(response)
            return
        
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
            embed = embeds.embed_paid_tickets(user, self.next_draw)
            message = await context.send(embed=embed)
            await message.add_reaction(emotes.X)
        else:
            await context.send(f"{user.mention}\nYou haven't bought any tickets yet!")

    @commands.command(aliases=['o'], brief='Show all your ticket orders')
    async def orders(self, context):
        user = context.author
        player = data.get_player(user)

        for order in player.ticket_orders:
            await self.send_ticket_order_embed(context, user, order)
        
        if not player.ticket_orders:
            await context.send(f'{user.mention}\nYou have no ticket orders!')

    async def draw_result(self, context):
        await self.block_orders()

        joined_players = data.get_joined_players(context)
        result = ball_machine.draw()

        embed = discord.Embed(title='Lottery Result')
        embed.timestamp = self.next_draw

        message = None
        while True:
            embed.color = colors.random_bright(embed.color)
            embed.description = '```%s```' % result.reveal()

            if not message:
                message = await context.send(embed=embed)
            else:
                await message.edit(embed=embed)
            
            self.pay_out_winners(joined_players, result)

            if result.revealed_all():
                break
            await asyncio.sleep(1)
        
        await self.announce_winners(context, joined_players, result)

        self.reset()
    
    def pay_out_winners(self, joined_players, result):
        for player in joined_players:
            won = player.check_ticket(result.last_revealed)
            user = self.bot.get_user(player.id)
        
            if won:
                _, multi = result.last_prize
                coins_won = won * multi
                player.pay_prize(coins_won)
    
    async def announce_winners(self, context, joined_players, result):
        for player in joined_players:
            user = self.bot.get_user(player.id)
            
            winning_tickets = result.compare_tickets(player)

            if not winning_tickets: continue

            winner_embed = discord.Embed(title=f'You Won! {user.name}') 
            winner_embed.set_thumbnail(url=user.avatar_url)
            winner_embed.color = colors.random_bright()
            winner_embed.timestamp = self.next_draw

            for prize, tickets in zip(draw_result.PRIZES, winning_tickets):
                prize_name = draw_result.get_prize_name(prize)
                _, multi = prize
                values = []
                for number, worth in tickets[::-1]:
                    prize_coins = worth * multi
                    value = f'`{number:02}`: **{worth}** × {multi:02} = **{prize_coins} coins**'
                    values.append(value)
                if values:
                    field = dict(name=prize_name, value='\n'.join(values))
                    winner_embed.add_field(**field)
            
            total_spendings = player.get_total_spendings()
            initial_balance = player.balance + total_spendings - player.total_winnings
            value = (
                f'Spent: {embeds.format_coins(total_spendings)}\n'
                f'Won : {embeds.format_coins(player.total_winnings)}\n'
                f'Before: {embeds.format_coins(initial_balance)}\n'
                f'After: {embeds.format_coins(player.balance)}'
            )
            winner_embed.add_field(name='Balance Status', value=value)

            message_args = dict(content=user.mention, embed=winner_embed)
            await context.send(**message_args) 

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if self.should_ignore_reaction(reaction, user):
            return

        message = reaction.message
        embed = message.embeds[0]
        player = data.get_player(user)

        if str(reaction) == emotes.X:
            await self.cancel_order(player, message)
        elif str(reaction) == emotes.MONEY_WINGS:
            self.schedule_next_draw(message)
            await self.buy_order(user, message)
            await self.wait_to_draw()
    
    async def cancel_order(self, player, message):
        player.remove_order(message)
        await message.delete()

    async def buy_order(self, user, message):
        player = data.get_player(user)
        order = player.find_order_by_message(message)
        if order:
            player.buy_ticket_order(order)
            player.remove_order(message)

            embed = embeds.embed_paid_tickets(user, self.next_draw)
            
            await message.edit(embed=embed)
            await message.remove_reaction(emotes.MONEY_WINGS, self.bot.user)
            await self.update_ticket_order_embeds(user)

    def schedule_next_draw(self, message):
        channel = message.channel
        guild = channel.guild
        self.guilds_announce_channel[guild.id] = channel.id

        if self.next_draw: return

        self.next_draw = ceil_datetime(datetime.now()).astimezone()
    
    async def wait_to_draw(self):
        if self.scheduled: return

        self.scheduled = True
        await discord.utils.sleep_until(self.next_draw)

        for guild_id, channel_id in self.guilds_announce_channel.items():
            channel = self.bot.get_channel(channel_id)
            await self.draw_result(channel)

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
            message = discord.utils.get(self.bot.cached_messages, id=message.id)
            order.message = message
            if not message: continue

            new_embed = embeds.embed_ticket_order(user, order, hide_buy_field=self.orders_blocked)
            await message.edit(embed=new_embed)
            
            has_buy_field = discord.utils.get(new_embed.fields, name=embeds.BUY_FIELD)
            has_buy_reaction = discord.utils.get(message.reactions, emoji=emotes.MONEY_WINGS)
            if has_buy_field and not has_buy_reaction:
                await message.remove_reaction(emotes.X, self.bot.user)
                await message.add_reaction(emotes.MONEY_WINGS)
                await message.add_reaction(emotes.X)
            elif not has_buy_field and has_buy_reaction:
                await message.remove_reaction(emotes.MONEY_WINGS, self.bot.user)

def add_to(bot):
    bot.add_cog(Lottery(bot))