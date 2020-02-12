import discord
import colors
import lotto

from discord.ext import commands
from lotto import data, level, embeds, as_coins

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players_stored_xp = {}
    
    @commands.command(aliases=['lvl', 'lv'])
    async def level(self, context):
        user = context.author
        embed = embeds.for_level(user)
        await context.send(embed=embed)
    
    def store_xp(self, player, xp:int):
        self.players_stored_xp[player] = self.players_stored_xp.get(player, 0) + xp
    
    async def add_stored_xp(self, context):
        for player, xp in self.players_stored_xp.items():
            await self.add_xp(context, player, xp)
            self.players_stored_xp[player] = 0
    
    async def add_xp(self, context, user_or_player, xp:int):
        user = data.get_user(self.bot, user_or_player)
        player = data.get_player(user_or_player)
        
        player.clear_level_up()
        player._add_xp(xp)
        if player.level_up:
            lines = [LEVEL_UP % player.level_up]

            old_max, new_max = map(lotto.get_max_tickets_for, player.level_up)
            if new_max > old_max:
                lines += [CAN_BUY % new_max]
                
            embed = embeds.for_level(user)
            lines += [embed.description]
            lines += [INCOME + as_coins(player.get_income(), backtick=True, suffix=False)]
            embed.description = '\n'.join(lines)
            await context.send(embed=embed)
    
    @commands.command()
    async def xp(self, context, xp:int):
        user = context.author
        await self.add_xp(context, user, xp)

LEVEL_UP = '**LEVEL UP!** `%s → %s`'
CAN_BUY = 'You can now buy `%s` tickets!'
INCOME = '**Income**: '

def add_to(bot):
    bot.add_cog(LevelSystem(bot))