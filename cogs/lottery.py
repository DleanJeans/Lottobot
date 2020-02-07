import asyncio
import discord
import pytz

import emotes
import colors

from discord.ext import commands
from datetime import datetime, timedelta
from lotto.player import Player
from lotto import data, embeds
from lotto import ticket_parser
from lotto import ball_machine, draw_result

BUY_INSTRUCTION = '''
**Syntax**: `lott buy [coins], [numbers]`
`numbers` have to be within `00` to `99`
_Example_: `lott buy 10, 20 30 40` 
buys 3 tickets `20` `30` and `40`
each costs **10** coins, totaling **30** coins
'''

BUY_SHORTHANDS = '''
**Shorthands**:
`a-b`: includes all the number between `a` and `b` and themselves
_Example_: `6-9` = `06` `07` `08` `09`

`~a`: includes `a` and its reversed number
_Example_: `~42` = `24` `42`

`a+(b)`: includes `a` and `b` adjecent numbers in each direction
`b` is `1` by default if not given
can be combined with `~`
_Example_: 
`80+` = `79` `80` `81` 
`80+5` = `75-85`
`~60+5` = `06` `55-65`
'''

BUY_DESCRIPTION = f'{BUY_INSTRUCTION}{BUY_SHORTHANDS}'.replace('*', '').replace('`', '').replace('_', '')
BUY_BRIEF = 'Buy tickets for this cycle'

TICKETS_BRIEF = 'Show all your tickets'

MORE_THAN_ZERO = 'Gimme more than **0** coins, bruh!'
WAIT_FOR_RESULT = 'Hold on a minute! The result is being announced right now!'

NO_TICKETS = "You haven't bought any tickets yet!"
LOTTERY_RESULT = 'Lottery Result'

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
        embed.color = colors.random_bright()
        embed.description = BUY_INSTRUCTION
        await context.send(embed=embed)

    @commands.command(aliases=['b'], brief=BUY_BRIEF, description=BUY_DESCRIPTION)
    async def buy(self, context, coins, *tickets):
        user = context.author

        if not tickets:
            await self.send_instruction(context)
            return
        
        coins = ticket_parser.parse_coins(coins)

        if coins == 'all':
            coins = data.get_player(user).balance
        elif coins == 'half':
            coins = data.get_player(user).balance / 2
        elif coins == None:
            await self.send_instruction(context)
            return
        
        if coins <= 0:
            await context.send(MORE_THAN_ZERO)
            return
        
        was_announcing = self.announcing
        if self.announcing:
            response = f'{user.mention}\n{WAIT_FOR_RESULT}'
            await context.send(response)
            while self.announcing:
                await asyncio.sleep(1)
        
        try:
            new_tickets = ticket_parser.parse_list(tickets)
        except ValueError as e:
            response = f'{user.mention}\n'
            response += '\n'.join(e.args)
            await context.send(response)
            return
        
        order = data.add_ticket_order(user, coins, new_tickets)
        await self.send_ticket_order_embed(context, user, order, was_announcing)
    
    @buy.error
    async def buy_error(self, context, error):
        if type(error) is commands.MissingRequiredArgument:
            await self.send_instruction(context)
        else:
            raise

    async def send_ticket_order_embed(self, context, user, order, mention=False):
        embed = embeds.embed_ticket_order(user, order)
        content = user.mention if mention else None

        message = await context.send(content=content, embed=embed)
        order.message = message
        can_buy = self.player_can_buy(user, order)

        if can_buy:
            await message.add_reaction(emotes.MONEY_WINGS)
        await message.add_reaction(emotes.X)

    def player_can_buy(self, user_or_player, order):
        if type(user_or_player) is Player:
            player = user_or_player
        else:
            user = user_or_player
            player = data.get_player(user)
        
        return player.can_buy(order) and not self.announcing

    @commands.command(aliases=['t', 'tix', 'tic', 'ticket'], brief=TICKETS_BRIEF)
    async def tickets(self, context):
        user = context.author
        player = data.get_player(user)
        if player.paid_tickets or player.ticket_orders:
            embed = embeds.embed_paid_tickets(user, self.next_draw)
            message = await context.send(embed=embed)
            await message.add_reaction(emotes.X)

            for order in player.ticket_orders:
                await self.send_ticket_order_embed(context, user, order)
        else:
            await context.send(f'{user.mention}\n{NO_TICKETS}')

    async def draw_result(self, context):
        await self.block_orders()

        joined_players = data.get_joined_players(context)
        result = ball_machine.draw()

        embed = discord.Embed(title=LOTTERY_RESULT)
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

            def is_list_empty(l):
                return all(map(is_list_empty, l)) if type(l) is list else False

            if is_list_empty(winning_tickets): continue

            winner_embed = embeds.embed_winner(user, winning_tickets)
            winner_embed.timestamp = self.next_draw

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
            if not message: continue
            message = discord.utils.get(self.bot.cached_messages, id=message.id)
            order.message = message

            new_embed = embeds.embed_ticket_order(user, order, self.announcing)
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