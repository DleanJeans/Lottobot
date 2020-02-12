import discord
import emotes
import colors
import lotto

from lotto import data, ticket_parser, level, as_coins

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
TICKET_ORDER_OF = 'Ticket Order of '
TICKETS_OF = 'Tickets of '

CANNOT_AFFORD = f'You\'re %s short!'
MAX_TICKET_COUNT = f'Your max ticket count is: **%s**'
RESULT_ANNOUNCING = 'The result is being announced right now!'
CANNOT_BUY_FIELD = 'Cannot Buy'

BEFORE = 'Before'
SPENT = 'Spent'
NEXT_DRAW_AT = 'Next Draw at'

YOU_WON = 'You Won!'
WELL_KINDA = 'Well, kinda...'
CONGRATS = 'Congrats!'

def create(footer_user=None, **kwargs):
    embed = discord.Embed(**kwargs)
    if 'color' not in kwargs:
        embed.color = colors.random()
    if footer_user:
        user = footer_user
        embed.set_footer(text=user.name, icon_url=user.avatar_url)
    return embed

def for_ticket_order(user, order, announcing=False):
    player = data.get_player(user)

    title = TICKET_ORDER_OF + user.name
    description = ticket_parser.format_as_description(order.tickets)

    can_buy = player.can_buy(order) and not announcing
    color = CAN_BUY_COLOR if can_buy else CANNOT_BUY_COLOR

    embed = create(title=title, description=description, color=color, footer_user=user)

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
        if not player.can_hold_more_tickets(order):
            reason = MAX_TICKET_COUNT % player.get_max_tickets()
        elif not player.can_afford(order):
            reason = CANNOT_AFFORD % as_coins(-balance_after)
            income = player.get_income()
            if balance < income:
                reason += '\n' + lotto.INCOME_TIP + as_coins(income)
        elif announcing:
            reason = RESULT_ANNOUNCING
        embed.add_field(name=CANNOT_BUY_FIELD, value=reason)

    return embed

def for_paid_tickets(user, next_draw=None):
    player = data.get_player(user)

    title = TICKETS_OF + user.name

    embed = create(title=title, color=discord.Color.green())

    tickets_by_price = player.group_paid_tickets()
    for price, tickets in tickets_by_price.items():
        desc = ticket_parser.format_as_description(tickets)
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

def for_winner(user, winning_tickets):
    player = data.get_player(user)

    winner_embed = create(title=YOU_WON, color=colors.random()) 
    winner_embed.set_thumbnail(url=user.avatar_url)

    for prize, tickets in zip(lotto.PRIZES, winning_tickets):
        prize_name = lotto.get_prize_name(prize)
        _, multi = prize
        values = []
        for number, worth in tickets[::-1]:
            prize_coins = worth * multi
            worth = as_coins(worth, suffix=False)
            prize_coins = as_coins(prize_coins)
            value = f'`{number:02}`: {worth} → {prize_coins}'
            values.append(value)
        if values:
            field = dict(name=prize_name, value='\n'.join(values))
            winner_embed.add_field(**field)
    
    total_spendings = player.get_total_spendings()
    initial_balance = player.balance + total_spendings - player.total_winnings
    change = player.total_winnings - total_spendings
    sign = '+' if change >= 0 else ''
    value = (
        f' {as_coins(initial_balance)}\n'
        f'-{as_coins(total_spendings)}\n'
        f'+{as_coins(player.total_winnings)}\n'
        f'({sign}{as_coins(change)})\n'
        f'={as_coins(player.balance)}'
    )
    winner_embed.add_field(name=BALANCE, value=value)

    winner_embed.title += ' ' + (WELL_KINDA if change <= 0 else CONGRATS)

    return winner_embed

def for_level(user):
    player = data.get_player(user)
    lvl = player.get_level()
    next_lvl = lvl + 1
    xp = player.xp
    gap = level.gap(lvl)
    total_xp_last_lvl = level.xp_for_level(lvl-1)
    xp_this_lvl = xp - total_xp_last_lvl

    embed = create(footer_user=user)
    embed.description = f'**Level {lvl}**: `{xp_this_lvl}/{gap} XP`'

    return embed