import discord
import data
import ticket_parser
import emotes

AFFORDABLE_COLOR = discord.Color.blue()
INAFFORDABLE_COLOR = discord.Color.orange()

BUY_FIELD = f'{emotes.MONEY_WINGS} Buy'
CLOSE_FIELD = f'{emotes.X} Close'

PAY_ORDER = 'Pay for these tickets'
CLOSE_ORDER = 'Close this order'

EACH_TICKET_COST = 'Each Ticket Cost'
TOTAL_COST = 'Total Cost'
BALANCE = 'Balance'
BALANCE_AFTER = 'Balance After'

TICKET_COUNT = 'Ticket Count'
TICKET_ORDER_OF = '\'s Ticket Order'
TICKETS_OF = '\' Tickets'

CLOSE_THIS_MESSAGE = 'Close this message'

def format_coins(coins):
    return f'**{coins}** coins'

def embed_ticket_order(user, order):
    title = user.name + TICKET_ORDER_OF
    full_list = ', '.join(map(str, order.tickets))
    description = ticket_parser.format_as_description(order.tickets)

    balance = data.get_balance(user)
    total_cost = order.total_cost()
    balance_after = balance - total_cost
    affordable = balance_after >= 0
    color = AFFORDABLE_COLOR if affordable else INAFFORDABLE_COLOR

    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=user.name, icon_url=user.avatar_url)

    coin_fields = {
        EACH_TICKET_COST: order.coins,
        TOTAL_COST: total_cost,
        BALANCE: balance,
        BALANCE_AFTER: balance_after
    }

    if len(order.tickets) == 1:
        coin_fields.pop(EACH_TICKET_COST)
    else:
        embed.add_field(name=TICKET_COUNT, value=str(len(order.tickets)))

    add_coin_fields(embed, coin_fields)

    if balance_after >= 0:
        embed.add_field(name=BUY_FIELD, value=PAY_ORDER)
    embed.add_field(name=CLOSE_FIELD, value=CLOSE_ORDER)

    return embed
    
def embed_paid_tickets(user):
    player = data.get_player(user)

    title = user.name + TICKETS_OF

    embed = discord.Embed(title=title, color=discord.Color.green())

    tickets_by_price = player.group_paid_tickets()
    for price, tickets in tickets_by_price.items():
        desc = ticket_parser.format_as_description(tickets)
        embed.add_field(name=format_coins(price), value=desc)

    embed.add_field(name=BALANCE, value=format_coins(player.balance))
    embed.add_field(name=CLOSE_FIELD, value=CLOSE_THIS_MESSAGE)

    return embed

def add_coin_fields(embed, coin_fields):
    for name, coins in coin_fields.items():
        embed.add_field(name=name, value=format_coins(coins))