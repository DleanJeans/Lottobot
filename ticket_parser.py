import re
import textwrap
import itertools

REGEX_RANGE = '(\d+)-(\d+)'
REGEX_SINGLE = '~*(\d+)\+{0,1}(\d*)'

MIN = 0
MAX = 99
BALL_FORMAT = '{:02}'.format

SHORTEN = '**Shorten**'
COUNT = '**Count**'
NOT_WITHIN = 'is not within `00` and `99`'

def backtick_every_word(string):
    return ' '.join(map('`{}`'.format, string.split(' ')))

def format_as_description(tickets, tickets_per_line=11):
    tickets = list(set(tickets))
    tickets = sorted(tickets)
    full_list = ' '.join(map(BALL_FORMAT, tickets))
    full_list = '\n'.join(textwrap.wrap(full_list, width=3*tickets_per_line))
    short_list = shorten_list(tickets)
    
    description = f'```{full_list}```\n'

    if short_list != full_list:
        short_list = backtick_every_word(short_list)
        description += f'{SHORTEN}: {short_list}\n'
    
    ticket_count = len(tickets)
    if ticket_count > 1:
        description += f'{COUNT}: {ticket_count}\n'

    return description

def shorten_list(tickets):
    output = []
    for r in list(ranges(tickets)):
        a, b = r
        if a == b:
            output.append(str(a))
        else:
            sep = '-' if abs(a-b) >= 2 else ' '
            output.append(f'{a}{sep}{b}')
    output = ' '.join(output)
    return output

def ranges(i):
    for a, b in itertools.groupby(enumerate(i), lambda pair: pair[1] - pair[0]):
        b = list(b)
        yield b[0][1], b[-1][1]

def valid(ticket):
    return MIN <= int(ticket) <= MAX

def clamp(ticket):
    return max(MIN, min(MAX, ticket))

def parse_range(match):
    ticket_range = list(map(int, match.groups()))
    ticket_range.sort()
    a, b = ticket_range
    for t in ticket_range:
        if not valid(t):
            raise ValueError(f'Range `{a}`-`{b}` {NOT_WITHIN}!')
    
    return [i for i in range(a, b+1)]

def parse_single(match):
    new_tickets = []
    center, extends = match.groups()
    ticket = match.string

    if not valid(center):
        raise ValueError(f'`{center}` {NOT_WITHIN}!')

    if '~' in ticket:
        reverse = center.zfill(2)[::-1]
        if int(reverse) != int(center):
            new_tickets.append(int(reverse))
    
    center = int(center)
    if '+' in ticket and not extends:
        extends = 1
    
    if extends:
        extends = int(extends)
        new_range = center - extends, center + extends
        a, b = map(clamp, new_range)

        new_tickets += [i for i in range(a, b + 1)]
    else:
        new_tickets.append(center)
    
    return new_tickets

REGEX_TO_FUNCTION = {
    REGEX_RANGE: parse_range,
    REGEX_SINGLE: parse_single
}

def parse_list(input_tickets):
    global first_error
    first_error = True
    tickets = []
    exceptions = []
    
    for ticket in input_tickets:
        try:
            new_tickets = detect_parse(ticket)
            tickets += new_tickets
        except ValueError as e:
            exceptions.append(e.args[0])

    tickets.sort()

    if exceptions:
        raise ValueError(*exceptions)

    return list(set(tickets))

first_error = True

def detect_parse(ticket):
    for regex, do in REGEX_TO_FUNCTION.items():
        match = re.match(regex, ticket)
        if match:
            new_tickets = do(match)
            return new_tickets
    
    global first_error
    error_msg = f'WTF is this bruh?' if first_error else 'And this?'
    first_error = False
    raise ValueError(f'{error_msg} `{ticket}`')