import re

REGEX_RANGE = '(\d+)-(\d+)'
REGEX_SINGLE = '~*(\d+)\+{0,1}(\d*)'
MIN = 0
MAX = 99

def format_list(tickets):
    if len(tickets) <= 1:
        tickets = map(str, tickets)
        return ' '.join(tickets)
    
    output = ''
    last_adjacent = False
    adjacent = False
    
    for t, next in zip(tickets, tickets[1:]):
        if not adjacent:
            output += f'{t} '
        
        adjacent = abs(t - next) == 1

        if not adjacent and last_adjacent:
            output += f'-{t} '
        last_adjacent = adjacent
    
    output = output.replace(' -', '-')
    return output.strip()

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
            raise ValueError(f'Range {a}-{b} is not within 00 and 99!')
    
    return [i for i in range(a, b+1)]

def parse_single(match):
    new_tickets = []
    center, extends = match.groups()
    ticket = match.string

    if not valid(center):
        raise ValueError(f'Ticket Order **{ticket}**: {center} is not within 00 to 99.')

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

def detect_parse(ticket):
    for regex, do in REGEX_TO_FUNCTION.items():
        match = re.match(regex, ticket)
        if match:
            new_tickets = do(match)
            return new_tickets
        
    raise ValueError(f'Ticket Order **{ticket}** ignored!')


def parse_list(input_tickets):
    tickets = []
    exceptions = []
    
    for ticket in input_tickets:
        try:
            new_tickets = detect_parse(ticket)
            tickets += new_tickets
        except Exception as e:
            exceptions.append(e.args[0])

    tickets.sort()

    if exceptions:
        raise ValueError(*exceptions)

    return tickets