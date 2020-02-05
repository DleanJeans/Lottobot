import discord
import data
import ticket_parser
import emotes

CAN_BUY_COLOR = discord.Color.blue()
CANNOT_BUY_COLOR = discord.Color.orange()

BUY_FIELD = f'{emotes.MONEY_WINGS} Buy'
CANCEL_FIELD = f'{emotes.X} Cancel'
CLOSE_FIELD = f'{emotes.X} Close'

UNIT_COST = 'One'
TOTAL_COST = 'Total'
BALANCE = 'Balance'

NOW = 'Now'
AFTER = 'After'
COST = 'Cost'

REACTIONS = 'Reactions'
TICKET_COUNT = 'Ticket Count'
TICKET_ORDER_OF = '\'s Ticket Order'
TICKETS_OF = '\' Tickets'

CANNOT_AFFORD = f'You\'re %s short!'
MAX_TICKET_COUNT = f'Your max ticket count is: **%s**'
RESULT_ANNOUNCING = 'The result is being announced right now!'
CANNOT_BUY_FIELD = 'Cannot Buy'

BEFORE = 'Before'
SPENT = 'Spent'
NEXT_DRAW_AT = 'Next Draw at'

def as_coins(coins):
    return f'**{coins}** coins'

def embed_ticket_order(user, order, announcing=False):
    player = data.get_player(user)

    title = user.name + TICKET_ORDER_OF
    description = ticket_parser.format_as_description(order.tickets)

    can_buy = player.can_buy(order) and not announcing
    color = CAN_BUY_COLOR if can_buy else CANNOT_BUY_COLOR

    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=user.name, icon_url=user.avatar_url)

    total_cost = order.total_cost()

    cost_value = (
        f'{UNIT_COST}: {as_coins(order.coins)}\n'
        f'{TOTAL_COST}: {as_coins(total_cost)}'
    )

    if order.coins == total_cost:
        cost_value = cost_value.split('\n')[1]

    embed.add_field(name=COST, value=cost_value)

    balance = player.balance
    balance_after = balance - total_cost

    balance_value = (
        f'{NOW}: {as_coins(balance)}\n'
        f'{AFTER}: {as_coins(balance_after)}'
    )

    embed.add_field(name=BALANCE, value=balance_value)

    reactions = ''
    if can_buy:
        reactions += BUY_FIELD + '\n'
    reactions += CANCEL_FIELD
    embed.add_field(name=REACTIONS, value=reactions)

    if not can_buy:
        reason = ''
        if not player.can_afford(order):
            reason = CANNOT_AFFORD % as_coins(-balance_after)
        elif not player.can_hold_more_tickets(order):
            reason = MAX_TICKET_COUNT % player.get_max_tickets()
        elif announcing:
            reason = RESULT_ANNOUNCING
        embed.add_field(name=CANNOT_BUY_FIELD, value=reason)

    return embed

def embed_paid_tickets(user, next_draw=None):
    player = data.get_player(user)

    title = user.name + TICKETS_OF

    embed = discord.Embed(title=title, color=discord.Color.green())

    tickets_by_price = player.group_paid_tickets()
    for price, tickets in tickets_by_price.items():
        desc = ticket_parser.format_as_description(tickets, 10)
        embed.add_field(name=as_coins(price), value=desc)

    spendings = player.get_total_spendings()
    balance_before = player.balance + spendings
    balance_value = (
        f'{as_coins(balance_before)}\n'
        f'-{as_coins(spendings)}\n'
        f'={as_coins(player.balance)}'
    )
    embed.add_field(name=BALANCE, value=balance_value)
    embed.add_field(name=REACTIONS, value=CLOSE_FIELD)

    if next_draw:
        embed.timestamp = next_draw
    
    footer_text = NEXT_DRAW_AT if next_draw else None
    embed.set_footer(text=footer_text, icon_url=user.avatar_url)

    return embed

def add_coin_fields(embed, coin_fields):
    for name, coins in coin_fields.items():
        embed.add_field(name=name, value=as_coins(coins))