ECONOMY = 'Economy'
LOTTERY = 'Lottery'
LEVEL_SYSTEM = 'LevelSystem'

from discord.ext import commands

member_converter = commands.MemberConverter()

async def convert_to_user(context, member):
    if member:
        try:
            user = await member_converter.convert(context, member)
        except:
            await context.send(f"Who's `{member}`?")
            return
    else:
        user = context.author
    return user