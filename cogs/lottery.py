import asyncio
import discord
import math

import emotes
import colors
import lotto
import cogs

from discord.ext import commands
from datetime import datetime, timedelta
from lotto.player import Player
from lotto import data, embeds, ticket_parser, ball_machine, level

BUY_INSTRUCTION = '''
**Syntax**: `lott buy [coins], [numbers]`
`numbers` have to be within `00` to `99`

**Example**: `lott buy 10, 20 30 40` 
buys 3 tickets `20` `30` and `40` 
with **10** coins, totaling **30** coins
the coins will be split if it's over your balance

**Shorthands**:
`42+` → `41 42 43`
`~42` → `42 24`
'''

BUY_DESCRIPTION = f'{BUY_INSTRUCTION}'.replace('*', '').replace('`', '').replace('_', '')
BUY_BRIEF = 'Buy tickets for this cycle'

TICKETS_BRIEF = 'Show all your tickets'

MORE_THAN_ZERO = 'Gimme more than **0** coins, bruh!'
WAIT_FOR_RESULT = 'Hold on a minute! The result is being announced right now!'

YOU_NO_TICKETS = "You haven't bought any tickets yet!"
THEY_NO_TICKETS = "has't bought any tickets yet!"
LOTTERY_RESULT = 'Lottery Result'

E_TIP = '**Tip**: Try `e` for big numbers. `e6` for 6 zeros. `1e6` is 1 million!'

RESULT_BRIEF = 'Show the last lottery result'

TRY_AGAIN_LATER = 'The bot is starting up!\nGo buy a ticket and try again later!'

ALL = 'all'
HALF = 'half'
SIX_ZEROES = '0' * 6

def ceil_datetime(dt, minutes=lotto.CYCLE_INTERVAL):
    delta = timedelta(minutes=minutes)
    return dt + (datetime.min - dt) % delta

class Lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reset()
        self.last_result = None
    
    def reset(self):
        self.scheduled = False
        self.next_draw = None
        self.announcing = False
        self.guilds_announce_channel = {}
        data.clear_players_tickets()
    
    async def block_orders(self):
        self.announcing = True
        players = data.get_joined_players()
        for p in players:
            user = self.bot.get_user(p.id)
            await self.update_ticket_order_embeds(user)
    
    async def send_instruction(self, context):
        embed = discord.Embed()
        embed.color = colors.random()
        embed.description = BUY_INSTRUCTION
        await context.send(embed=embed)
    
    @commands.command(aliases=['res', 'rslt', 'rs'], brief=RESULT_BRIEF)
    async def result(self, context):
        embed = embeds.create(title='Last Lottery Result')
        if self.last_result and not self.announcing:
            embed.description = '```%s```' % self.last_result
            embed.timestamp = self.last_result.timestamp

            user = context.author
            player = data.get_player(user)
            tickets = player.last_tickets
            if not tickets:
                your_tickets = 'No tickets bought last time.'
            else:
                your_tickets = []
                for t in tickets.keys():
                    prize = self.last_result.get_ticket_prize(t)
                    if not prize:
                        prize = 'No Prize', 0
                    tickets[t] = prize
                tickets = { t: p for t, p in sorted(tickets.items(), key=lambda item: item[1][1], reverse=True) }

                for t, prize in tickets.items():
                    prize = lotto.get_prize_name(prize)
                    your_tickets += [f'{t:02} - {prize}']
                your_tickets = '\n'.join(your_tickets)
                your_tickets = f'```{your_tickets}```'
            embed.add_field(name='Your Tickets', value=your_tickets)
        else:
            embed.description = TRY_AGAIN_LATER

        await context.send(embed=embed)

    @commands.command(aliases=['b'], brief=BUY_BRIEF, description=BUY_DESCRIPTION)
    async def buy(self, context, coins, *tickets):
        user = context.author

        if not tickets:
            await self.send_instruction(context)
            return
        
        coins = ticket_parser.parse_coins(coins)

        tip = None
        if SIX_ZEROES in str(coins):
            tip = E_TIP
        
        coins_str = str(coins).lower()

        player = data.get_player(user)
        balance = player.balance

        if coins_str in [ALL, HALF]:
            if balance == 0:
                balance = player.get_income()
            if coins_str == ALL:
                coins = balance
            elif coins_str == HALF:
                coins = balance / 2
        elif coins == None:
            await self.send_instruction(context)
            return
        
        try:
            new_tickets = ticket_parser.parse_list(tickets)
        except ValueError as e:
            response = f'{user.mention}\n'
            response += '\n'.join(e.args)
            await context.send(response)
            return
        
        ticket_count = len(new_tickets)
        total_cost = coins * ticket_count
        divided_cost = math.floor(coins // ticket_count)
        if total_cost > balance and divided_cost <= balance:
            coins = divided_cost
        
        if coins <= 0:
            await context.send(MORE_THAN_ZERO)
            return
        
        was_announcing = self.announcing
        if self.announcing:
            response = f'{user.mention}\n{WAIT_FOR_RESULT}'
            await context.send(response)
            while self.announcing:
                await asyncio.sleep(1)
        
        order = data.add_ticket_order(user, coins, new_tickets)
        await self.send_ticket_order_embed(context, user, order, was_announcing, tip)

        if player.balance == 0:
            await self.bot.get_cog(cogs.ECONOMY).income(context)
    
    @buy.error
    async def buy_error(self, context, error):
        if type(error) is commands.MissingRequiredArgument:
            await self.send_instruction(context)
        else:
            raise

    async def send_ticket_order_embed(self, context, user, order, mention=False, tip=None):
        embed = embeds.for_ticket_order(user, order)
        content = user.mention if mention else ''
        if tip:
            if content:
                content += '\n'
            content += tip

        message = await context.send(content=content, embed=embed)
        order.message = message
        can_buy = self.player_can_buy(user, order)

        if can_buy:
            await message.add_reaction(emotes.MONEY_WINGS)
        await message.add_reaction(emotes.X)

        return message

    def player_can_buy(self, user_or_player, order):
        if type(user_or_player) is Player:
            player = user_or_player
        else:
            user = user_or_player
            player = data.get_player(user)
        
        return player.can_buy(order) and not self.announcing

    @commands.command(aliases=['t', 'tix', 'tic', 'ticket'], brief=TICKETS_BRIEF)
    async def tickets(self, context, member=None):
        user = await cogs.convert_to_user(context, member)
        if not user: return

        player = data.get_player(user)
        if player.paid_tickets or player.ticket_orders:
            embed = embeds.for_paid_tickets(user, self.next_draw)
            message = await context.send(embed=embed)
            await message.add_reaction(emotes.X)

            if user != context.author: return
            for order in player.ticket_orders:
                await self.send_ticket_order_embed(context, user, order)
        else:
            response = f'{user.mention}\n{YOU_NO_TICKETS}' if user == context.author \
                else f'**{user.name}** {THEY_NO_TICKETS}'
            await context.send(response)

    async def draw_result(self, context):
        await self.block_orders()

        joined_players = data.get_joined_players(context)
        result = ball_machine.draw()
        result.timestamp = self.next_draw

        embed = discord.Embed(title=LOTTERY_RESULT, timestamp=self.next_draw)

        message = None
        while True:
            embed.color = colors.random(embed.color)
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
        self.last_result = result
    
    def pay_out_winners(self, joined_players, result):
        for player in joined_players:
            won = player.check_ticket(result.last_revealed)
            user = self.bot.get_user(player.id)
        
            if won:
                _, multi = result.last_prize
                coins_won = won * multi
                player.pay_prize(coins_won)

                multi_index = lotto.MULTIPLIERS.index(multi)
                xp_for_prize = level.PRIZES_XP[multi_index]
                self.bot.get_cog(cogs.LEVEL_SYSTEM).store_xp(player, xp_for_prize)
    
    async def announce_winners(self, context, joined_players, result):
        for player in joined_players:
            user = self.bot.get_user(player.id)
            
            winning_tickets = result.compare_tickets(player)

            def is_list_empty(l):
                return all(map(is_list_empty, l)) if type(l) is list else False

            if is_list_empty(winning_tickets): continue

            winner_embed = embeds.for_winner(user, winning_tickets)
            winner_embed.timestamp = self.next_draw

            message_args = dict(content=user.mention, embed=winner_embed)
            await context.send(**message_args) 

            await self.bot.get_cog(cogs.LEVEL_SYSTEM).add_stored_xp(context)

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
            if self.announcing: return
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
            if not player.paid_tickets:
                await self.bot.get_cog(cogs.LEVEL_SYSTEM).add_xp(message.channel, player, level.BUY_XP)
            
            player.buy_ticket_order(order)
            player.remove_order(message)

            embed = embeds.for_paid_tickets(user, self.next_draw)
            
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
            if not message: continue
            message = discord.utils.get(self.bot.cached_messages, id=message.id)
            order.message = message

            new_embed = embeds.for_ticket_order(user, order, self.announcing)
            await message.edit(embed=new_embed)

            can_buy = self.player_can_buy(player, order)
            has_buy_reaction = discord.utils.get(message.reactions, emoji=emotes.MONEY_WINGS)

            if can_buy and not has_buy_reaction:
                await message.remove_reaction(emotes.X, self.bot.user)
                await message.add_reaction(emotes.MONEY_WINGS)
                await message.add_reaction(emotes.X)
            elif not can_buy and has_buy_reaction:
                await message.remove_reaction(emotes.MONEY_WINGS, self.bot.user)

def add_to(bot):
    bot.add_cog(Lottery(bot))