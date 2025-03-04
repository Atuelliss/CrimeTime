import asyncio
import logging
import discord
import random
import typing as t
import math

from redbot.core.utils.chat_formatting import humanize_timedelta
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
from .common.models import DB, User
from .dynamic_menu import DynamicMenu

log = logging.getLogger("red.crimetime")


class CrimeTime(commands.Cog):
    """
    A crime mini-game cog for Red-DiscordBot.
    """
    __author__ = "Jayar(Vainne)"
    __version__ = "0.0.1"

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.db: DB = DB()
        self.recent_targets = {} # track the most recent targets
        self.target_limit = 5 # number of targets to track against

        # Cooldowns separated by target or not target.
        self.pvpcooldown = commands.CooldownMapping.from_cooldown(1, 30, commands.BucketType.user)
        self.pvecooldown = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.user)
        # Cooldown for investment command, cash to gold/diamonds. 12hours.
        self.investcooldown = commands.CooldownMapping.from_cooldown(1, 43200, commands.BucketType.user)
        # Future cooldown spot for Robberies.

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
    async def ctwealth(self, ctx: commands.Context, member: discord.Member = None):
        """Checks the total assets of a User."""
        member  = member or ctx.author
        guildsettings = self.db.get_conf(ctx.guild)
        user = guildsettings.get_user(member)
        balance = user.balance
        gold = user.gold
        gold_value = 2500
        diamond = user.diamond
        diamond_value = 5000
        gold_total = gold * gold_value
        diamond_total = diamond * diamond_value
        total_value = balance + gold_total + diamond_total
        await ctx.send(f"**{member.display_name}**\n-=-=-=-=-=-=-=-=-=-=-\n**Cash Balance**: ${balance}\n**Gold Bars**: {gold} - ${gold_total}\n**Diamonds**: {diamond} - ${diamond_total}\n-=-=-=-=-=-=-=-=-=-=-\nTotal Wealth: ${total_value}")

    # Convert Cash to Gold or Diamonds
    @commands.group(invoke_without_command=True)
    async def ctinvest(self, ctx: commands.Context):
        """Ability for players to convert currency forms."""
        await ctx.send(f"Please specify a valid subcommand, e.g.:\n`$ctinvest gold (number of bars you want).`\n`$ctinvest diamonds (how many diamonds you want).`")

    @ctinvest.command()
    async def gold(self, ctx: commands.Context, amount: int, member: discord.Member):
        """Allows a Player to convert cash to Gold Bars."""
        # Ensure a valid amount is entered
        if amount <= 0:
            await ctx.send("You must enter a positive amount of gold bars to invest in.")
            return
        # Default to author if no target is provided
        member = ctx.author
        gold_value = 2500
        bar_count = amount
        cash_needed = bar_count * gold_value
        # Check investment cooldown for player
        investbucket = self.investcooldown.get_bucket(ctx.message) # Cooldown for Cash conversion.

        # Get user data
        guildsettings = self.db.get_conf(ctx.guild)
        user = guildsettings.get_user(member)
        
        # Check to see if user has enough cash.
        if user.balance < cash_needed:
            await ctx.send("You do not have enough cash for that transaction.")
            return

        secondsleft = investbucket.update_rate_limit() # Add invest timer to user.
        if secondsleft:
            wait_time = humanize_timedelta(seconds=int(secondsleft))
            return await ctx.send(f"You must wait {wait_time} until you can invest in more assets!")

        # Transfer currency
        user.balance -= cash_needed
        user.gold += bar_count
        self.save()
        await ctx.send(f"You invested ${cash_needed} into {bar_count} gold bars!!")

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
        r_wins = user.r_wins
        r_losses = user.r_losses
        r_ratio_str = user.r_ratio_str
        h_wins = user.h_wins
        h_losses = user.h_losses
        h_ratio_str = user.h_ratio_str

        # Determine Attack Bonuses against other players.
        if p_ratio >= 5:
            p_bonus = 0.25
        elif p_ratio >= 3.01:
            p_bonus = 0.2
        elif p_ratio >= 3:
            p_bonus = 0.15
        elif p_ratio >= 2:
            p_bonus = 0.1
        elif p_ratio >= 1:
            p_bonus = 0.05
        elif p_ratio == 0:
            p_bonus = 0.0
        elif p_ratio >= -1:
            p_bonus = -0.05
        elif -1 > p_ratio >= -2:
            p_bonus = -0.1
        elif -2 > p_ratio >= -3:
            p_bonus = -0.15
        elif p_ratio <= -3.01:
            p_bonus = -0.2
        elif p_ratio <= -5:
            p_bonus = -0.25
        await ctx.send(f"**{member.display_name}**\nBalance: ${balance}\nP-Win/Loss Ratio: {p_ratio_str}[{p_ratio}]\nP-Bonus: {p_bonus}") #\nRobbery Win/Loss Ratio: {r_ratio_str}")

    # Actually run the MUG command.
    @commands.command()
    async def mug(self, ctx: commands.Context, target: discord.Member = None):
        """This command can be used for both PvE and PvP mugging."""

        if target is not None and target == ctx.author: # Targetting yourself does nothing.
            await ctx.send("You reach into your pockets and grab your wallet, what now?")
            return
        if target is not None and target.bot: # No targeting Bots!
            await ctx.send("You cannot target the Bots!")
            return
        
        pvpbucket = self.pvpcooldown.get_bucket(ctx.message) # Cooldown for Mug pve
        pvebucket = self.pvecooldown.get_bucket(ctx.message) # Cooldown for Mug pvp
        author    = ctx.author
        #Rating = Easy
        stranger1 = ["a smart-mouthed boy", "a grouchy old man", "an elderly woman", "a sweet foreign couple",  "a lady-of-the-night", 
                    "a random stranger", "a stuffy-looking banker", "a creepy little girl", "a sad-faced clown", "a Dwarf in a penguin costume", 
                    "a sleep-deprived college Student", "a scruffy Puppy with a wallet in it's mouth", "a hyper Ballerina", 
                    "a boy dressed as a Stormtrooper", "a girl dressed as Princess Leia", "a baby in a stroller", "a group of drunk frat boys", 
                    "a poor girl doing the morning walk of shame", "another mugger bad at the job", "a man in a transparent banana costume",
                    "an angry jawa holding an oddly thrusting mechanism", "two Furries fighting over an 'Uwu'", "a dude in drag posting a thirst-trap on tiktok"]
        #Rating = Medium
        stranger2 = ["a man in a business suit", "a doped-out gang-banger", "an off-duty policeman", "a local politician", 
                     "a scrawny meth-head missing most of his teeth", "Chuck Schumer's personal assistant"]
        #Rating = Hard
        stranger3 = ["Elon Musk!!", "Bill Clinton!!", "Vladamir Putin!!", "Bigfoot!!", "Steve Job's Corpse", "Roseanne Barr!!", "Borat!!", 
                     "a shirtless Florida-man", "Megatron", "John Wick's dog"]
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
                    #mugger_user.pve_win += 1
                    await ctx.send(f"**{author.display_name}** successfully mugged *{strangerchoice}* and made off with ${reward}!")
                else:
                    #mugger_user.pve_loss += 1
                    await ctx.send(f"**{author.display_name}** looked around for someone to mug but found no one nearby...")
            elif difficulty_choice == stranger2:
                strangerchoice = random.choice(difficulty_choice)
                if pve_attack > rating_medium:
                    reward = random.randint(26, 50)
                    mugger_user.balance += reward
                    #mugger_user.pve_win += 1
                    await ctx.send(f"**{author.display_name}** successfully mugged *{strangerchoice}* and made off with ${reward}!")
                else:
                    #mugger_user.pve_loss += 1
                    await ctx.send(f"**{author.display_name}** looked around for someone to mug but found no one nearby...")
            elif difficulty_choice == stranger3:
                strangerchoice = random.choice(difficulty_choice)
                if pve_attack > rating_hard:
                    reward = random.randint(51, 75)
                    mugger_user.balance += reward
                    #
                    await ctx.send(f"**{author.display_name}** successfully mugged *{strangerchoice}* and made off with ${reward}!")
                else:
                    #mugger_user.pve_loss += 1
                    await ctx.send(f"**{author.display_name}** looked around for someone to mug but found no one nearby...")
        else:
            # If we are here, user has targeted another player.
              
            # If we here, user targeted a player and now we check allowed status.
            target_user = guildsettings.get_user(target)
            if mugger_user.balance < 50:
                await ctx.send(f"You have less than $50 and cannot mug other Players yet!.")
                return
            if target_user.balance < 50:
                await ctx.send(f"The target has less than $50 and isn't worth mugging.")
                return
            pvp_defend = random.uniform(0, 1) + target_user.p_bonus #need to add in armor bonus later

            # Track pvp targets and make sure new target is allowed, this prevents attacking the same person over and over.
            # Check if the target is valid and enforce unique targets
            if target_user:
                recent_targets = self.recent_targets.get(ctx.author.id, [])
    
                if target.id in recent_targets:
                    required_targets_left = self.target_limit - len(recent_targets)
                    if required_targets_left > 0:
                        await ctx.send(f"You cannot target {target.display_name} again until you mug at least {required_targets_left} other players.")
                        return

            # Update recent targets for the author
            if target.id not in recent_targets:
                recent_targets.append(target.id)
                # Enforce the target limit
                if len(recent_targets) > self.target_limit:
                    recent_targets.pop(0)  # Remove the oldest target
            self.recent_targets[ctx.author.id] = recent_targets
            # PvP Mugging, Attacking another User who is not under the minimum amount.

            # Run the actual contested check.    
            secondsleft = pvpbucket.update_rate_limit() # Add pvp timer to user.
            if secondsleft:
                wait_time = humanize_timedelta(seconds=int(secondsleft))
                return await ctx.send(f"You must wait {wait_time} until you can target another Player!")
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
                #Make no changes from here for the pvp aspect.
        self.save()

# Ability for players to clear their win/loss ratios.
    @commands.command()
    async def mugclear(self, ctx: commands.Context, target: discord.Member = None):
        """Reset a User's PvP Wins and Losses to 0 for an incrimental cost."""
        # Cost to clear ratio for the first time
        first_free = 0
        base_cost = 500
        # Default to author if no target is provided
        target = target or ctx.author

        # Prevent using on others
        if target != ctx.author:
            await ctx.send("You cannot use this on others.")
            return

        # Get guild settings and user data
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)

        # Calculate cost based on how many times the user has reset
        cost = first_free if target_user.mugclear_count == 0 else base_cost * target_user.mugclear_count

        # Check if player can afford to reset
        if target_user.balance < cost:
            await ctx.send("You cannot afford to reset your ratio at this time.")
            return  # Stop execution if they can't afford it

        # Ask for confirmation
        await ctx.send(f"This will completely reset all of your Win/Loss stats for ${cost}. This can NOT be reverted.\nType 'yes' to confirm.")

        try:
            msg = await ctx.bot.wait_for("message", timeout=30, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            if msg.content.lower() != "yes":
                await ctx.send("Action canceled. PvP stats were not reset.")
                return
        except asyncio.TimeoutError:
            await ctx.send("Confirmation timed out. PvP stats were not reset.")
            return

        # Reset user's stats
        target_user.p_wins = 0
        target_user.p_losses = 0
        target_user.mugclear_count += 1  # Corrected increment
        target_user.balance -= cost #Removes the cost of the clear from the users balance.

        await ctx.send("Your PvP Wins/Losses have been reset to 0.")
        self.save()

# Ability for Players to give currency to others.
    @commands.group(invoke_without_command=True)
    async def ctgive(self, ctx: commands.Context):
        """Ability for players to transfer currency forms."""
        await ctx.send("Please specify a valid subcommand, e.g., `!ctgive cash @user amount`.")

    @ctgive.command()
    async def cash(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Allows a Player to give a form of Currency to another user."""
        
        # Ensure target is not None and not the giver
        if target == ctx.author:
            await ctx.send("You cannot do this alone; you must target another user.")
            return

        # Get user data
        guildsettings = self.db.get_conf(ctx.guild)
        giver = guildsettings.get_user(ctx.author)
        target_user = guildsettings.get_user(target)

        # Validate amount
        if amount <= 0:
            await ctx.send("You must send a positive amount.")
            return

        # Ensure giver has enough balance
        if giver.balance < amount:
            await ctx.send("You do not have that much to give!!")
            return

        # Transfer currency
        giver.balance -= amount
        target_user.balance += amount
        self.save()
        await ctx.send(f"You gave {target.mention} ${amount}.")

##########  Admin Commands  ##########

    # This group allows the Administrator to CLEAR amounts, not set them.
    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)  # Only Admins can use this command    
    async def ctclear(self, ctx: commands.Context):
        """Configure CrimeTime User Data"""

    @ctclear.command() # Clears a User's total data file.
    async def all(self, ctx: commands.Context, target: discord.Member):
        '''Reset a User's total Stat pool to 0.'''
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.balance = 0
        target_user.gold = 0
        target_user.diamond = 0
        target_user.p_wins = 0
        target_user.p_losses = 0
        target_user.r_wins = 0
        target_user.r_losses = 0
        target_user.h_wins = 0
        target_user.h_losses = 0
        target_user.pop_up_wins = 0
        target_user.pop_up_losses = 0
        await ctx.send(f"**{target.display_name}**'s complete record has been reset to 0.")
        self.save()

    @ctclear.command() # Clears a User's cash balance
    async def balance(self, ctx: commands.Context, target: discord.Member):
        """Reset a User's Cash Balance to 0."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.balance = 0
        await ctx.send(f"**{target.display_name}**'s Balance has been reset to 0.")
        self.save()

    @ctclear.command() # Clears a User's Gold-Bar balance
    async def gold(self, ctx: commands.Context, target: discord.Member):
        """Reset a User's Gold Bar Count to 0."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.gold = 0
        await ctx.send(f"**{target.display_name}**'s Gold Bar count has been reset to 0.")
        self.save()
    
    @ctclear.command() # Clears a User's Diamond count balance
    async def diamonds(self, ctx: commands.Context, target: discord.Member):
        """Reset a User's Diamond count to 0."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.diamond = 0
        await ctx.send(f"**{target.display_name}**'s Diamond count has been reset to 0.")
        self.save()
 
    @ctclear.command() # Clears a User's PvP wins and losses.
    async def pstats(self, ctx: commands.Context, target: discord.Member):
        '''Reset a User's PvP Wins and Losses to 0.'''
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.p_wins = 0
        target_user.p_losses = 0
        await ctx.send(f"**{target.display_name}**'s PvP Wins/Losses have been reset to 0.")
        self.save()
    
    @ctclear.command() # Clear's a Users Rob wins and losses.
    async def rstats(self, ctx: commands.Context, target: discord.Member):
        '''Reset a User's Robbery Wins and Losses to 0.'''
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.r_wins = 0
        target_user.r_losses = 0
        await ctx.send(f"**{target.display_name}**'s Robbery Wins/Losses have been reset to 0.")
        self.save()
    
    @ctclear.command() # Clear's a Users Heist wins and losses.
    async def hstats(self, ctx: commands.Context, target: discord.Member):
        '''Reset a User's Heist Wins and Losses to 0.'''
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.h_wins = 0
        target_user.h_losses = 0
        await ctx.send(f"**{target.display_name}**'s Heist Wins/Losses have been reset to 0.")
        self.save()

    # This group allows the Administrator to SET the users stats to specified amounts.
    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)  # Only Admins can use this command    
    async def ctset(self, ctx: commands.Context):
        """Configure CrimeTime User Data"""

    @ctset.command() # Set a User's Cash Balance to a specific number.
    async def balance(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Cash Balance to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative balance!")
            return
        target_user.balance = amount
        await ctx.send(f"**{target.display_name}**'s Balance have been set to {amount}.")
        self.save()

    @ctset.command() # Set a User's Gold Bar Count to a specific number.
    async def gold(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Gold Bar count to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative balance!")
            return
        target_user.gold = amount
        await ctx.send(f"**{target.display_name}**'s Gold Bars have been set to {amount}.")
        self.save()
    
    @ctset.command() # Set a User's Diamond Count to a specific number.
    async def diamonds(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Diamond count to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative balance!")
            return
        target_user.diamond = amount
        await ctx.send(f"**{target.display_name}**'s Diamond count has been set to {amount}.")
        self.save()
    
    @ctset.command() # Set a User's PvP wins.
    async def pwin(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's PvP Wins to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative amount!")
            return
        target_user.p_wins = amount
        await ctx.send(f"**{target.display_name}**'s PvP Mug Wins have been set to {amount}.")
        self.save()
    
    @ctset.command() # Set a User's PvP losses.
    async def ploss(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's PvP Losses to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative amount!")
            return
        target_user.p_losses = amount
        await ctx.send(f"**{target.display_name}**'s PvP Mug Losses have been set to {amount}.")
        self.save()

    @ctset.command() # Set a User's Rob wins.
    async def rwin(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Robbery Wins to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative amount!")
            return
        target_user.r_wins = amount
        await ctx.send(f"**{target.display_name}**'s Robbery wins have been set to {amount}.")
        self.save()
    
    @ctset.command() # Set a User's Rob losses.
    async def rloss(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Robbery loss to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative amount!")
            return
        target_user.r_losses = amount
        await ctx.send(f"**{target.display_name}**'s Robbery losses have been set to {amount}.")
        self.save()

    @ctset.command() # Set a User's Heist wins.
    async def hwin(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Heist Wins to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative amount!")
            return
        target_user.h_wins = amount
        await ctx.send(f"**{target.display_name}**'s Heist wins have been set to {amount}.")
        self.save()
    
    @ctset.command() # Set a User's Heist losses.
    async def hloss(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Heist loss to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative amount!")
            return
        target_user.h_losses = amount
        await ctx.send(f"**{target.display_name}**'s Heist losses have been set to {amount}.")
        self.save()

    @commands.command() # Leaderboard Commands for Mugging
    async def muglb(self, ctx: commands.Context, stat: t.Literal["balance", "wins", "ratio"]):
        """Displays leaderboard for Player Mugging stats."""
        guildsettings = self.db.get_conf(ctx.guild)
        users: dict[int, User] = guildsettings.users
        if stat == "balance":
            sorted_users: list[tuple[int, User]] = sorted(users.items(), key=lambda x: x[1].balance, reverse=True)
            sorted_users: list[tuple[int, User]] = [i for i in sorted_users if i[1].balance] # Removes users with 0 for balance.
        elif stat == "wins":
            sorted_users: list[tuple[int, User]] = sorted(users.items(), key=lambda x: x[1].p_wins, reverse=True)
            sorted_users: list[tuple[int, User]] = [i for i in sorted_users if i[1].p_wins]
        else: # Ratio
            sorted_users: list[tuple[int, User]] = sorted(users.items(), key=lambda x: x[1].p_ratio, reverse=True)
            sorted_users: list[tuple[int, User]] = [i for i in sorted_users if i[1].p_ratio]

        embeds = []
        pages = math.ceil(len(sorted_users) / 15)
        start = 0
        stop = 15
        for index in range(pages):
            stop = min(stop, len(sorted_users))
            txt = ""
            for position in range(start, stop):
                user_id, user_obj = sorted_users[position]
                if stat == "balance":
                    value = user_obj.balance
                elif stat == "wins":
                    value = user_obj.p_wins
                else:
                    value = user_obj.p_ratio
                txt += f"{position + 1}. <@{user_id}> `{value}`\n"
            title = f"{stat.capitalize()} Leaderboard!"
            embed = discord.Embed(description=txt, title=title)
            embed.set_footer(text=f"Page {index+1}/{pages}")
            embeds.append(embed)
            start += 15
            stop += 15

        await DynamicMenu(ctx, embeds).refresh()