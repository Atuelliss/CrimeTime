import discord
from redbot.core import commands, Config
import random
from typing import Optional

class Mug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        # Cooldowns separated by target or not target
        self.pvpcooldown = commands.CooldownMapping.from_cooldown(1, 15, commands.BucketType.user)
        self.pvecooldown = commands.CooldownMapping.from_cooldown(1, 3600, commands.BucketType.user)


        # Default user data
        default_user = {
            "balance": 0,  
            "wins": 0,    
            "losses": 0    
        }
        self.config.register_user(**default_user)
    
    @commands.command()
    async def mug(self, ctx: commands.Context, target: Optional[discord.Member] = None):
        pvpbucket = self.pvpcooldown.get_bucket(ctx.message)
        pvebucket = self.pvpcooldown.get_bucket(ctx.message)
        author = ctx.author
        if target is None or target == author:  # No target or self-mugging
            secondsleft = pvebucket.update_rate_limit()
            if secondsleft:
                return await ctx.send(f"You must wait {secondsleft} before you can reuse this command.")
            # If we are here, user can mug an npc.

        elif target and target.id == self.bot.user.id:
            # If we are here, the user targeted the bot.
            return await ctx.send(f"You cannot target Bots!")
        else:
            # If we are here, user has targeted another player.
            secondsleft = pvpbucket.update_rate_limit()
            if secondsleft:
                return await ctx.send(f"You must wait {secondsleft} until you can target another Player!")
            # If we here, user targeted a player and does not have to wait to attack another player.
            



            ...Run randomized check to determine which NPC type player gets to go against(simple, easy, medium, hard)
            ...
            ...Generate a Cooldown for timer using npc-cooldown-timeframe
