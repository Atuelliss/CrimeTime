import asyncio
import logging
import discord
import random

from redbot.core.utils.chat_formatting import humanize_timedelta
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
from .common.models import DB


log = logging.getLogger("red.crimetime")


class CrimeTime(commands.Cog):
    """
    A crime mini-game cog for Red-DiscordBot.
    """
    __author__ = "Jayar"
    __version__ = "0.0.1"

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.db: DB = DB()
        # Cooldowns separated by target or not target
        self.pvpcooldown = commands.CooldownMapping.from_cooldown(1, 30, commands.BucketType.user)
        self.pvecooldown = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.user)

        # States
        self._saving = False

    def format_help_for_context(self, ctx: commands.Context):
        helpcmd = super().format_help_for_context(ctx)
        txt = "Version: {}\nAuthor: {}".format(self.__version__, self.__author__)
        return f"{helpcmd}\n\n{txt}"

    async def red_delete_data_for_user(self, *args, **kwargs):
        return

    async def red_get_data_for_user(self, *args, **kwargs):
        return

    async def cog_load(self) -> None:
        asyncio.create_task(self.initialize())

    async def initialize(self) -> None:
        await self.bot.wait_until_red_ready()
        self.db = await asyncio.to_thread(DB.from_file, cog_data_path(self) / "db.json")
        log.info("Config loaded")

    def save(self) -> None:
        async def _save():
            if self._saving:
                return
            try:
                self._saving = True
                await asyncio.to_thread(self.db.to_file, cog_data_path(self) / "db.json")
            except Exception as e:
                log.exception("Failed to save config", exc_info=e)
            finally:
                self._saving = False

        asyncio.create_task(_save())

    # Check balance and stats
    @commands.command()
    async def mugcheck(self, ctx: commands.Context, member: discord.Member = None):
        """Checks the Balance, Wins/Losses, and Ratio of a User."""
        member  = member or ctx.author
        guildsettings = self.db.get_conf(ctx.guild)
        user = guildsettings.get_user(member)
        p_wins = user.p_wins
        p_losses = user.p_losses
        p_ratio = user.p_ratio
        p_ratio_str = user.p_ratio_str
        balance = user.balance
        # r_wins = user.r_wins
        # r_losses = user.r_losses

        # Determine Attack Bonuses against other players.
        if p_ratio >= 3.01:
            p_bonus = 0.5
        elif p_ratio >= 3:
            p_bonus = 0.3
        elif p_ratio >= 2:
            p_bonus = 0.2
        elif p_ratio >= 1:
            p_bonus = 0.1
        elif p_ratio == 0:
            p_bonus = 0.0
        elif p_ratio >= -1:
            p_bonus = -0.1
        elif -1 > p_ratio >= -2:
            p_bonus = -0.2
        elif -2 > p_ratio >= -3:
            p_bonus = -0.3
        elif p_ratio <= -3.01:
            p_bonus = -0.5
        await ctx.send(f"**{member.display_name}**\nBalance: ${balance}\nP-Win/Loss Ratio: {p_ratio_str}\nP-Bonus: {p_bonus}")

    # Actually run the MUG command.
    @commands.command()
    async def mug(self, ctx: commands.Context, target: discord.Member = None):
        """This command can be used for both PvE and PvP mugging."""
        if target is not None and target == ctx.author:
            await ctx.send("You reach into your pockets and grab your wallet, what now?")
            return
        if target is not None and target.bot:
            await ctx.send("You cannot target the Bots!")
            return
        pvpbucket = self.pvpcooldown.get_bucket(ctx.message)
        pvebucket = self.pvecooldown.get_bucket(ctx.message)
        author    = ctx.author
        #Rating = Easy
        stranger1 = ["a smart-mouthed boy", "a grouchy old man", "an elderly woman", "a sweet foreign couple",  "a lady-of-the-night", 
                    "a random stranger", "a stuffy-looking banker", "a creepy little girl", "a sad-faced clown", "a Dwarf in a penguin costume", 
                    "a sleep-deprived college Student", "a scruffy Puppy with a wallet in it's mouth", "a hyper Ballerina", 
                    "a boy dressed as a Stormtrooper", "a girl dressed as Princess Leia", "a baby in a stroller", "a group of drunk frat boys", 
                    "a poor girl doing the morning walk of shame", "another mugger bad at the job", "a man in a transparent banana costume"]
        #Rating = Medium
        stranger2 = ["a man in a business suit", "a doped-out gang-banger", "an off-duty policeman", "a local politician", 
                     "a scrawny meth-head missing most of his teeth", ]
        #Rating = Hard
        stranger3 = ["Elon Musk!!", "Bill Clinton!!", "Vladamir Putin!!", "Bigfoot!!", "Steve Job's Corpse", "Roseanne Barr!!", "Borat!!"]
        rating_easy    = 0.2
        rating_medium  = 0.5
        rating_hard    = 0.7
        difficulty_choice = random.choice([stranger1, stranger2, stranger3])
        guildsettings = self.db.get_conf(ctx.guild)
        mugger_user = guildsettings.get_user(ctx.author)
        pve_attack = random.uniform(0, 1) 
        pvp_attack = random.uniform(0, 1) + mugger_user.p_bonus #need to add in weapon bonus later.

        if target is None:
            secondsleft = pvebucket.update_rate_limit()
            if secondsleft:
                wait_time = humanize_timedelta(seconds=int(secondsleft))
                return await ctx.send(f"You must wait {wait_time} before you can reuse this command.")
            # If we are here, no timer and user can mug an npc.
            if difficulty_choice == stranger1:
                strangerchoice = random.choice(difficulty_choice)
                if pve_attack > rating_easy:
                    reward = random.randint(1, 25)
                    mugger_user.balance += reward
                    await ctx.send(f"**{author.display_name}** successfully mugged *{strangerchoice}* and made off with ${reward}!")
                else:
                    await ctx.send(f"**{author.display_name}** looked around for someone to mug but found no one nearby...")
            elif difficulty_choice == stranger2:
                strangerchoice = random.choice(difficulty_choice)
                if pve_attack > rating_medium:
                    reward = random.randint(26, 50)
                    mugger_user.balance += reward
                    await ctx.send(f"**{author.display_name}** successfully mugged *{strangerchoice}* and made off with ${reward}!")
                else:
                    await ctx.send(f"**{author.display_name}** looked around for someone to mug but found no one nearby...")
            elif difficulty_choice == stranger3:
                strangerchoice = random.choice(difficulty_choice)
                if pve_attack > rating_hard:
                    reward = random.randint(51, 75)
                    mugger_user.balance += reward
                    await ctx.send(f"**{author.display_name}** successfully mugged *{strangerchoice}* and made off with ${reward}!")
                else:
                    await ctx.send(f"**{author.display_name}** looked around for someone to mug but found no one nearby...")
        else:
            # If we are here, user has targeted another player.
            secondsleft = pvpbucket.update_rate_limit()
            if secondsleft:
                wait_time = humanize_timedelta(seconds=int(secondsleft))
                return await ctx.send(f"You must wait {wait_time} until you can target another Player!")
            
            # If we here, user targeted a player and now we check allowed status.
            target_user = guildsettings.get_user(target)
            if mugger_user.balance < 50:
                await ctx.send(f"You have less than $50 and cannot mug other Players yet!.")
                return
            if target_user.balance < 50:
                await ctx.send(f"The target has less than $50 and isn't worth mugging.")
                return
            pvp_defend = random.uniform(0, 1) + target_user.p_bonus #need to add in armor bonus later
            
            # PvP Mugging, Attacking another User who is not under the minimum amount.
            if pvp_attack > pvp_defend:
                mug_amount = min(int(target_user.balance * 0.03), 1000)
                mugger_user.balance += mug_amount
                target_user.balance -= mug_amount
                await ctx.send(f"You attack {target} with everything you've got!\nYou have overwhelmed them this time and made off with ${mug_amount}!\nYou WON!!")
                #+1 pwin to attacker, +1 ploss to target
                mugger_user.p_wins += 1
                target_user.p_losses += 1
            elif pvp_attack < pvp_defend:
                await ctx.send(f"You attack {target} and find them well prepared!\nYou have failed this time!")
                #+1 ploss to attacker, +1 pwin to target
                mugger_user.p_losses += 1
                target_user.p_wins += 1
            elif pvp_attack == pvp_defend:
                await ctx.send(f"You attack {target} and find that you are equally matched!\nYou flee before you suffer any losses.")
                #Make no changes from here.
        self.save()

    ##########  Admin Commands  ##########
    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)  # Only Admins can use this command    
    async def ctset(self, ctx: commands.Context):
        """Configure CrimeTime User Data"""

    @ctset.command()
    async def clearbal(self, ctx: commands.Context, target: discord.Member):
        """Reset a User's Cash Balance to 0."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.balance = 0
        await ctx.send(f"**{target.display_name}**'s Balance have been reset to 0.")
        self.save()
    
    @ctset.command()
    async def setbal(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Reset a User's Cash Balance to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative balance!")
            return
        target_user.balance = amount
        await ctx.send(f"**{target.display_name}**'s Balance have been reset to {amount}.")
        self.save()

    @ctset.command()
    async def clearstat(self, ctx: commands.Context, target: discord.Member):
        '''Reset a User's PvP Wins and Losses to 0.'''
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.p_wins = 0
        target_user.p_losses = 0
        await ctx.send(f"**{target.display_name}**'s P-Wins/Losses have been reset to 0.")
        self.save()