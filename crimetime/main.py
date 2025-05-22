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
#from blackmarket import all_items

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
        self.pvpcooldown = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.user)
        self.pvecooldown = commands.CooldownMapping.from_cooldown(1, 30, commands.BucketType.user)
        # Cooldown for investment command, cash to gold/diamonds. 12hours.
        self.investcooldown = commands.CooldownMapping.from_cooldown(1, 43200, commands.BucketType.user)
        # Cooldown for Blitz command, once per hour players can join each other attacking things.
        self.blitzcooldown = commands.CooldownMapping.from_cooldown(1, 3600, commands.BucketType.user)
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

##### Crimetime Info Message
    @commands.command()
    async def crimetime(self, ctx: commands.Context):
        """Sends an embedded message with information on the overall game."""
    
    # Check if the bot has permission to send embeds
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            return await ctx.send("I need the 'Embed Links' permission to display this message properly.")
        try:
            info_embed = discord.Embed(
                title="What is CrimeTime?", 
                description="A criminal mini-game cog for Red-DiscordBot created by Jayar(aka-Vainne).", 
                color=0xffd700)
            info_embed.add_field(
                name="*What is the purpose of the game?*",
                value="Crimetime is a Discord game designed to allow Players to take on the role of a Criminal and attempt to gain as much wealth as possible through various means.\n \nThe game came about as a joke at first on the Vertyco Ark Servers but has since expanded in scope after interest from Players was shown. It is currently in development and is nowhere near complete yet.",
                inline=False)
            info_embed.add_field(
                name="*The current commands available for use in the game are:*",
                value="`$mug` - Command to mug NPCs and Players.\n`$mugcheck` - Checks a User's Cash Balance and Ratio.\n`$mugclear` - Resets your stats for a fee.\n`$ctwealth` - Displays total wealth $ assets of a User.\n`$ctgive` - Transfer assets to another Player.\n`$ctinvest` - Convert Cash to Gold Bars or Gems.\n`$ctliquidate` - Convert Bars or Gems to Cash.",
                inline=False)
            await ctx.send(embed=info_embed)
        except discord.HTTPException:
            await ctx.send("An error occurred while sending the message. Please try again later.")

#Cttarget command, displays most recent targets of Mug
    @commands.command(aliases=["cttarget"])
    async def display_my_target_list(self, ctx: commands.Context):
        '''Prints out a brief list of the user's most recent target list.'''
        member = ctx.author
        guild = ctx.guild
        guildsettings = self.db.get_conf(guild)
        user = guildsettings.get_user(member)

        # Convert user IDs to display names with IDs
        recent_target_ids = user.recent_targets
        recent_targets = []

        for uid in recent_target_ids:
            target = guild.get_member(uid)
            if target:
                recent_targets.append(f"{target.display_name} ({uid})")
            else:
                recent_targets.append(f"Unknown User ({uid})")

        target_list = "\n".join(recent_targets) if recent_targets else "no one recently"
        await ctx.send(f"-=-=-=-=-=-=-=-=-=-=-=-=-=-\n*You have recently attacked:*\n-=-=-=-=-=-=-=-=-=-=-=-=-=-\n{target_list}\n-=-=-=-=-=-=-=-=-=-=-=-=-=-\nTry attacking others NOT on this list to continue.")

# CtInvest function
    # Convert Cash to Gold or Gemstones
    @commands.group(invoke_without_command=True)
    async def ctinvest(self, ctx: commands.Context):
        """Ability for players to convert currency forms."""
        await ctx.send("Please specify a valid subcommand, e.g.:\n"
                       "`.ctinvest bars <amount>`\n"
                       "`.ctinvest gems <amount>`")

    @ctinvest.command(name="bars")
    async def invest_bars(self, ctx: commands.Context, amount: int = None):
        """Allows a Player to convert cash to Gold Bars."""
        member = ctx.author
        investbucket = self.investcooldown.get_bucket(ctx.message)
        guildsettings = self.db.get_conf(ctx.guild)
        user = guildsettings.get_user(member)  
        if user is None:
            await ctx.send("User data not found. Please try again later.")
            return
        if amount is None:
            await ctx.send("You must specify the amount of gold bars to invest in.")
            return
        if amount <= 0:
            await ctx.send("Please enter a valid number of gold bars to invest in.")
            return

        gold_value = 2500
        cash_needed = amount * gold_value

        secondsleft = investbucket.update_rate_limit()
        if user.balance < cash_needed:
            await ctx.send(f"You do not have the ${cash_needed} needed for that transaction.")
            return
        if secondsleft:
            wait_time = humanize_timedelta(seconds=int(secondsleft))
            await ctx.send(f"You must wait {wait_time} before investing again.")
            return
        else:
            user.balance -= cash_needed
            user.gold_bars += amount
            self.save()
            if amount == 1:
                await ctx.send(f"You invested ${cash_needed} into {amount} gold bar!\nYour investment is safe from mugging for now!")
            else:
                await ctx.send(f"You invested ${cash_needed} into {amount} gold bars!\nYour investment is safe from mugging for now!")

    @ctinvest.command(name="gems")
    async def invest_gems(self, ctx: commands.Context, amount: int = None):
        """Allows a Player to convert cash to gems."""
        member = ctx.author
        investbucket = self.investcooldown.get_bucket(ctx.message)
        guildsettings = self.db.get_conf(ctx.guild)
        user = guildsettings.get_user(member)
        if user is None:
            await ctx.send("User data not found. Please try again later.")
            return
        if amount is None:
            await ctx.send("You must specify the amount of gems to invest in.")
            return
        if amount <= 0:
            await ctx.send("Please enter a valid number of gems to invest in.")
            return

        gem_value = 5000
        cash_needed = amount * gem_value

        secondsleft = investbucket.update_rate_limit()
        if user.balance < cash_needed:
            await ctx.send(f"You do not have the ${cash_needed} for that transaction.")
            return
        if secondsleft:
            wait_time = humanize_timedelta(seconds=int(secondsleft))
            await ctx.send(f"You must wait {wait_time} before investing again.")
            return        
        else:
            user.balance -= cash_needed
            user.gems_owned += amount
            self.save()
            if amount == 1:
                await ctx.send(f"You invested ${cash_needed} into {amount} gem!\nYour investment is safe from mugging for now!")
            else:
                await ctx.send(f"You invested ${cash_needed} into {amount} gems!\nYour investment is safe from mugging for now!")

    @ctinvest.command(name="b2g")
    async def bars_to_gems(self, ctx: commands.Context, amount: int = None):
        """Allows a Player to convert Gold Bars to Gems."""
        member = ctx.author
        investbucket = self.investcooldown.get_bucket(ctx.message)
        guildsettings = self.db.get_conf(ctx.guild)
        user = guildsettings.get_user(member)  
        if user is None:
            await ctx.send("User data not found. Please try again later.")
            return
        if amount is None:
            await ctx.send("You must specify the amount of gold bars to invest in.")
            return
        if amount <= 0:
            await ctx.send("Please enter a valid number of gold bars to invest in.")
            return
        if amount % 2 != 0:
            await ctx.send("You must input an even number of gold bars. (2 bars = 1 gem)")
            return
        if user.gold_bars < amount:
            await ctx.send("You do not have enough gold bars for that transaction.")
            return
        gems_to_add = amount // 2
        user.gold_bars -= amount
        user.gems_owned += gems_to_add
        self.save()
        await ctx.send(f"You successfully converted {amount} gold bars into {gems_to_add} gems!")
     
# ctLiquidate
    # Convert Assets to Cash
    @commands.group(invoke_without_command=True, aliases=["ctld"])
    async def ctliquidate(self, ctx: commands.Context):
        """Ability for players to convert currency forms."""
        await ctx.send("Please specify a valid subcommand, e.g.:\n"
                       "`.ctliquidate bars <amount>`\n"
                       "`.ctliquidate gems <amount>`")

    @ctliquidate.command(name="bars")
    async def liquidate_bars(self, ctx: commands.Context, amount: int = None):
        """Allows a Player to convert Gold Bars to Cash."""
        member = ctx.author
        guildsettings = self.db.get_conf(ctx.guild)
        user = guildsettings.get_user(member)
        if user is None:
            await ctx.send("User data not found. Please try again later.")
            return
        if amount is None:
            await ctx.send("You must specify the amount of gold bars to convert.")
            return
        if amount <= 0:
            await ctx.send("Please enter a valid number of gold bars to convert.")
            return
        
        gold_value = 2500
        cash_payout = amount * gold_value

        if user.gold_bars < amount:
            await ctx.send("You do not have enough gold bars for that transaction.")
            return
        else:
            user.balance += cash_payout
            user.gold_bars -= amount
            self.save()
            if amount == 1:
                await ctx.send(f"You converted {amount} bar into ${cash_payout}!")
            else:
                await ctx.send(f"You converted {amount} bars into ${cash_payout}!")

    @ctliquidate.command(name="gems")
    async def liquidate_gems(self, ctx: commands.Context, amount: int = None):
        """Allows a Player to convert gems to cash."""
        member = ctx.author
        guildsettings = self.db.get_conf(ctx.guild)
        user = guildsettings.get_user(member)
        if user is None:
            await ctx.send("User data not found. Please try again later.")
            return
        if amount is None:
            await ctx.send("You must specify the amount of gems to liquidate.")
            return
        if amount <= 0:
            await ctx.send("Please enter a valid number of gems to liquidate.")
            return       

        gem_value = 5000
        cash_payout = amount * gem_value

        if user.gems_owned < amount:
            await ctx.send("You do not have enough gems for that transaction.")
            return
        else:
            user.balance += cash_payout
            user.gems_owned -= amount
            self.save()
            if amount == 1:
                await ctx.send(f"You converted {amount} gem into ${cash_payout}!")
            else:
                await ctx.send(f"You converted {amount} gems into ${cash_payout}!")

###### "Check" commands:
    # Check balance and stats specifically attributed to the Mug command.
    async def update_pbonus(self, ctx: commands.Context, member: discord.Member) -> None:
        """Recalculate and update a user's P-bonus based on their win/loss ratio."""
        guildsettings = self.db.get_conf(ctx.guild)
        user = guildsettings.get_user(member)
        p_ratio = user.p_ratio
                
        # Determine Player's Ratio-Bonuses for attack rolls.
        if p_ratio >= 5:
            user.p_bonus = 0.25
        elif p_ratio >= 3.01:
            user.p_bonus = 0.2
        elif p_ratio >= 3:
            user.p_bonus = 0.15
        elif p_ratio >= 2:
            user.p_bonus = 0.1
        elif p_ratio >= 1:
            user.p_bonus = 0.05
        elif p_ratio == 0:
            user.p_bonus = 0.0
        elif p_ratio >= -1:
            user.p_bonus = -0.05
        elif -1 > p_ratio >= -2:
            user.p_bonus = -0.1
        elif -2 > p_ratio >= -3:
            user.p_bonus = -0.15
        elif p_ratio <= -3.01:
            user.p_bonus = -0.2
        elif p_ratio <= -5:
            user.p_bonus = -0.25
        self.save()
    
    # Check balance and stats specifically attributed to the Mug command.
    @commands.command()
    async def ctstat(self, ctx: commands.Context, member: discord.Member = None):
        """Displays Player's wealth, gear, and stats."""
        member  = member or ctx.author
        guildsettings = self.db.get_conf(ctx.guild)
        user = guildsettings.get_user(member)
        cash = user.balance
        bars = user.gold_bars
        bar_value = bars * 2500
        gems = user.gems_owned
        gem_value = gems * 5000
        total_wealth = cash + bar_value + gem_value
        # gear_bonus = str("Attack Bonus: Unused / Defense Bonus: Unused")
        # head_armor = str("Future Use")
        # chest_armor = str("Future Use")
        # leg_armor = str("Future Use")
        # foot_armor = str("Future Use")
        # weapon_slot = str("Future Use")
        # consume_slot = str("Future Use")
        p_wins = user.p_wins
        p_loss = user.p_losses
        p_ratio = user.p_ratio
        p_bonus = user.p_bonus
        # p_ratio_str = user.p_ratio_str
        balance = user.balance
        r_wins = user.r_wins
        r_loss = user.r_losses
        r_ratio = user.r_ratio_str
        h_wins = user.h_wins
        h_loss = user.h_losses
        h_ratio = user.h_ratio_str
        await ctx.send(f"------------------------------------------------------\n**[Player Information]**\nName: {member}\nLevel: {user.player_level}\nExp: {user.player_exp}\nToNextLevel: {user.tnl_exp}\n------------------------------------------------------\n**[Wealth]**\nGems: {gems} : ${gem_value}\nGold: {bars}  : ${bar_value}\nCash: ${balance}\nTotal Wealth: ${total_wealth}\n------------------------------------------------------\n**[Gear & Item Bonuses]**\n(Head)       - Future Use\n(Chest)      - Future Use\n(Legs)        - Future Use\n(Feet)        - Future Use\n(Weapon)    - Future Use\n(Consumable) - Future Use\n \nAttack Bonus : (Future Use)\nDefense Bonus: (Future Use)\n------------------------------------------------------\n**[Stats & Ratios]**\nPvP Stats     - {p_wins}/{p_loss} : {p_ratio}\nRobbery Stats - {r_wins}/{r_loss} : {r_ratio}\nHeist Stats   - {h_wins}/{h_loss} : {h_ratio}\n \nCurrent P-Bonus: {p_bonus}\n------------------------------------------------------")


    # Check total wealth of all currencies.
    @commands.command()
    async def ctwealth(self, ctx: commands.Context, member: discord.Member = None):
        """Checks the total assets of a User."""
        member  = member or ctx.author
        guildsettings = self.db.get_conf(ctx.guild)
        user = guildsettings.get_user(member)
        cash = user.balance
        gold = user.gold_bars
        gold_value = 2500
        gems = user.gems_owned
        gem_value = 5000
        gold_total = gold * gold_value
        gem_total = gems * gem_value
        total_value = cash + gold_total + gem_total
        await ctx.send(f"**{member.display_name}**\n-=-=-=-=-=-=-=-=-=-=-\n**Cash Balance**: ${cash}\n**Gold Bars**: {gold} - ${gold_total}\n**Gems**: {gems} - ${gem_total}\n-=-=-=-=-=-=-=-=-=-=-\nTotal Wealth: ${total_value}")

    # Check balance and stats specifically attributed to the Mug command.
    @commands.command()
    async def mugcheck(self, ctx: commands.Context, member: discord.Member = None):
        """Checks the Balance, Wins/Losses, and Ratio of a User."""
        member  = member or ctx.author
        guildsettings = self.db.get_conf(ctx.guild)
        await self.update_pbonus(ctx, member)
        user = guildsettings.get_user(member)        
        p_ratio = user.p_ratio
        p_ratio_str = user.p_ratio_str
        p_bonus = user.p_bonus
        balance = user.balance
        r_wins = user.r_wins
        r_losses = user.r_losses
        r_ratio_str = user.r_ratio_str
        h_wins = user.h_wins
        h_losses = user.h_losses
        h_ratio_str = user.h_ratio_str        
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
                    "a poor girl doing the morning walk of shame", "another mugger who's bad at their job", "a man in a transparent banana costume",
                    "an angry jawa holding an oddly-thrusting mechanism", "two Furries fighting over an 'Uwu'",
                    "a dude in drag posting a thirst-trap on tiktok", "a mighty keyboard-warrior with cheetoh dust on his face", "a goat-hearder",
                    "Stormtrooper TK-421 who's firing at you and missing every shot", "an escaped mental patient oblivious to their surroundings",
                    "a Mogwai doused in water", "a tiny fairy trying to eat an oversized grape"]
        #Rating = Medium
        stranger2 = ["a man in a business suit", "a doped-out gang-banger", "an off-duty policeman", "a local politician", 
                     "a scrawny meth-head missing most of his teeth", "Chuck Schumer's personal assistant", "the Villainess Heiress", 
                     "an Elvis Presley impersonator shaking his hips to a song", "E.T. trying to hitchike home", "some juggling seals balancing on beach balls",
                     "an elderly woman just trying to cross the street", "a ten-year old little punk", "a meth-gator from the Florida swamps", 
                     "a Canadian Goose with squinty eyes", "Kano from Mortal Kombat, down on his luck", "a Jordanian terrorist searching for the Zohan",
                     "a clothed Carcharodontosaurus, wiping his runny nose with a kleenex", "Bart Simpson coming out of a firework stand"]
        #Rating = Hard
        stranger3 = ["Elon Musk leaving a DOGE meeting", "Bill Clinton, walking with his zipper down", "Vladamir Putin, humming 'Putin on the ritz'", "Bigfoot!!", "Steve Job's Corpse", 
                     "Roseanne Barr running from a BET awards show", "Borat!!", "a shirtless Florida-man", "Megatron", "John Wick's dog", "Bill Murray in a tracksuit with a cigar", 
                     "Joe Rogan", "Michelle Obama eating an ice-cream cone", "Will Smith's right-hand", "Macho-Man Randy Savage, 'Oooooh yeeeah'", "Greta Thunberg chasing cow farts", 
                     "Bill Murray in a zombie costume staring into the distance", "Mrs. Doubtfire awkwardly running to help someone", "90-year old Hulk Hogan in his iconic red/yellow wrestling gear",
                     "Forest Gump screaming, 'How are you run-nang so fast'"]
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
                    reward = random.randint(1, 35)
                    mugger_user.balance += reward
                    mugger_user.pve_win += 1                             
                    await ctx.send(f"**{author.display_name}** successfully mugged *{strangerchoice}* and made off with ${reward}!")
#Temp                    mugger_user.player_exp += 1 # +1 to Player Experience
                else:
                    mugger_user.pve_loss += 1
                    await ctx.send(f"**{author.display_name}** looked around for someone to mug but found no one nearby...")
            elif difficulty_choice == stranger2:
                strangerchoice = random.choice(difficulty_choice)
                if pve_attack > rating_medium:
                    reward = random.randint(36, 65)
                    mugger_user.balance += reward
                    mugger_user.pve_win += 1                    
                    await ctx.send(f"**{author.display_name}** successfully mugged *{strangerchoice}* and made off with ${reward}!")
#Temp                    mugger_user.player_exp += 2 # +2 to Player Experience
                else:
                    mugger_user.pve_loss += 1                    
                    await ctx.send(f"**{author.display_name}** looked around for someone to mug but found no one nearby...")
            elif difficulty_choice == stranger3:
                strangerchoice = random.choice(difficulty_choice)
                if pve_attack > rating_hard:
                    reward = random.randint(66, 95)
                    mugger_user.balance += reward
                    mugger_user.pve_win += 1                    
                    await ctx.send(f"**{author.display_name}** successfully mugged *{strangerchoice}* and made off with ${reward}!")
#Temp                    mugger_user.player_exp += 3 # +3 to Player Experience
                else:
                    mugger_user.pve_loss += 1                    
                    await ctx.send(f"**{author.display_name}** looked around for someone to mug but found no one nearby...")
        else:
            # If we here, user targeted a player and now we check allowed status.
            target_user = guildsettings.get_user(target)
            if mugger_user.balance < 50:
                await ctx.send(f"You have less than $50 and cannot mug other Players yet!.")
                return
            if target_user.balance < 50:
                await ctx.send(f"The target has less than $50 and isn't worth mugging.")
                return
            # PvP Mugging, Attacking another User who is not under the minimum amount.
            pvp_defend = random.uniform(0, 1) + target_user.p_bonus #need to add in armor bonus later

            # Track pvp targets and make sure new target is allowed, this prevents attacking the same person over and over.
            # Check if the target is valid and enforce unique targets
            # Get the list of recent targets from the user's data
            recent_targets = mugger_user.recent_targets

            if target.id in recent_targets:
                await ctx.send(f"You have already mugged {target.display_name} recently. Mug other players to clear your target list!")
                return
            
            # Check the pvp timer.    
            secondsleft = pvpbucket.update_rate_limit() # Add pvp timer to user.
            if secondsleft:
                wait_time = humanize_timedelta(seconds=int(secondsleft))
                return await ctx.send(f"You must wait {wait_time} until you can target another Player!")
            # Add the new target to the list
            recent_targets.append(target.id)
            # Keep only the last 5
            if len(recent_targets) > 5:
                recent_targets.pop(0)
            # Save back to the user
            mugger_user.recent_targets = recent_targets
            # Run the actual contested check.
            if pvp_attack > pvp_defend:
                mug_amount = min(round(target_user.balance * 0.07), 1000)
#Temp                mugger_user.player_exp += 5 # +5 to Player Experience
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

    @ctgive.command(name="cash")
    async def give_cash(self, ctx: commands.Context, target: discord.Member, amount: int):
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

    @ctgive.command(name="bars")
    async def give_gold_bars(self, ctx: commands.Context, target: discord.Member, amount: int):
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
        if giver.gold_bars < amount:
            await ctx.send("You do not have that much to give!!")
            return

        # Transfer currency
        giver.gold_bars -= amount
        target_user.gold_bars += amount
        self.save()
        if amount == 1:
            await ctx.send(f"You gave {target.mention} {amount} gold bar.")
        else:
            await ctx.send(f"You gave {target.mention} {amount} gold bars.")

##########  Admin Commands  ##########
    # Manually update a users P-Bonus
    @commands.command()
    @commands.admin_or_permissions(manage_guild=True)  # Only Admins can use this command
    async def pbupdate(self, ctx: commands.Context, member: discord.Member = None):
        """Checks the Balance, Wins/Losses, and Ratio of a User."""
        member  = member or ctx.author
        guildsettings = self.db.get_conf(ctx.guild)
        await self.update_pbonus(ctx, member)
        await ctx.send(f"{member.display_name}'s PvP bonus has been updated to {guildsettings.get_user(member).p_bonus}")

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
        target_user.gold_bars = 0
        target_user.gems_owned = 0
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

    @ctclear.command(name="balance") # Clears a User's cash balance
    async def clear_balance(self, ctx: commands.Context, target: discord.Member):
        """Reset a User's Cash Balance to 0."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.balance = 0
        await ctx.send(f"**{target.display_name}**'s Balance has been reset to 0.")
        self.save()

    @ctclear.command(name="bars") # Clears a User's Gold-Bar balance
    async def clear_bars(self, ctx: commands.Context, target: discord.Member):
        """Reset a User's Gold Bar Count to 0."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.gold_bars = 0
        await ctx.send(f"**{target.display_name}**'s Gold Bar count has been reset to 0.")
        self.save()
    
    @ctclear.command(name="gems") # Clears a User's Gem count balance
    async def clear_gems(self, ctx: commands.Context, target: discord.Member):
        """Reset a User's Gem count to 0."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.gems_owned = 0
        await ctx.send(f"**{target.display_name}**'s Gem count has been reset to 0.")
        self.save()
 
    @ctclear.command(name="pstats") # Clears a User's PvP wins and losses.
    async def clear_pstats(self, ctx: commands.Context, target: discord.Member):
        '''Reset a User's PvP Wins and Losses to 0.'''
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.p_wins = 0
        target_user.p_losses = 0
        await ctx.send(f"**{target.display_name}**'s PvP Wins/Losses have been reset to 0.")
        self.save()
    
    @ctclear.command(name="rstats") # Clear's a Users Rob wins and losses.
    async def clear_rstats(self, ctx: commands.Context, target: discord.Member):
        '''Reset a User's Robbery Wins and Losses to 0.'''
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_user.r_wins = 0
        target_user.r_losses = 0
        await ctx.send(f"**{target.display_name}**'s Robbery Wins/Losses have been reset to 0.")
        self.save()
    
    @ctclear.command(name="hstats") # Clear's a Users Heist wins and losses.
    async def clear_hstats(self, ctx: commands.Context, target: discord.Member):
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

    @ctset.command(name="view") # View a Users info.
    async def view_player(self, ctx: commands.Context, target: discord.Member):
        """Checks the total info of a User."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        target_exp = target_user.player_exp
        target_level = target_user.player_level
        await ctx.send(f"-=-=-=-=-=-=-=-=-=-=-\n**{target.display_name}**\n-=-=-=-=-=-=-=-=-=-=-\nLevel - {target_level}\nExp    - {target_exp}")

    @ctset.command(name="balance") # Set a User's Cash Balance to a specific number.
    async def set_balance(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Cash Balance to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative balance!")
            return
        target_user.balance = amount
        await ctx.send(f"**{target.display_name}**'s Balance have been set to {amount}.")
        self.save()

    @ctset.command(name="bars") # Set a User's Gold Bar Count to a specific number.
    async def set_bars(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Gold Bar count to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative balance!")
            return
        target_user.gold_bars = amount
        await ctx.send(f"**{target.display_name}**'s Gold Bars have been set to {amount}.")
        self.save()
    
    @ctset.command(name="gems") # Set a User's Gem Count to a specific number.
    async def set_gems(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Gems count to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative balance!")
            return
        target_user.gems_owned = amount
        await ctx.send(f"**{target.display_name}**'s Gem count has been set to {amount}.")
        self.save()
    
    @ctset.command(name="pwin") # Set a User's PvP wins.
    async def set_pwin(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's PvP Wins to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative amount!")
            return
        target_user.p_wins = amount
        await ctx.send(f"**{target.display_name}**'s PvP Mug Wins have been set to {amount}.")
        self.save()
    
    @ctset.command(name="ploss") # Set a User's PvP losses.
    async def set_ploss(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's PvP Losses to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative amount!")
            return
        target_user.p_losses = amount
        await ctx.send(f"**{target.display_name}**'s PvP Mug Losses have been set to {amount}.")
        self.save()

    @ctset.command(name="rwin") # Set a User's Rob wins.
    async def set_rwin(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Robbery Wins to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative amount!")
            return
        target_user.r_wins = amount
        await ctx.send(f"**{target.display_name}**'s Robbery wins have been set to {amount}.")
        self.save()
    
    @ctset.command(name="rloss") # Set a User's Rob losses.
    async def set_rloss(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Robbery loss to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative amount!")
            return
        target_user.r_losses = amount
        await ctx.send(f"**{target.display_name}**'s Robbery losses have been set to {amount}.")
        self.save()

    @ctset.command(name="hwin") # Set a User's Heist wins.
    async def set_hwin(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Heist Wins to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative amount!")
            return
        target_user.h_wins = amount
        await ctx.send(f"**{target.display_name}**'s Heist wins have been set to {amount}.")
        self.save()
    
    @ctset.command(name="hloss") # Set a User's Heist losses.
    async def set_hloss(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Set a User's Heist loss to specified amount."""
        guildsettings = self.db.get_conf(ctx.guild)
        target_user = guildsettings.get_user(target)
        if amount < 0:
            await ctx.send("You cannot set a negative amount!")
            return
        target_user.h_losses = amount
        await ctx.send(f"**{target.display_name}**'s Heist losses have been set to {amount}.")
        self.save()

# Admin-Initiated Events
    @commands.group(invoke_without_command=True)
    @commands.admin_or_permissions(manage_guild=True)  # Only Admins can use this command
    async def ctevent(self, ctx: commands.Context):
        """Ability for Admins to initiate a group event."""
        await ctx.send("Please specify a valid subcommand, e.g.:\n"
                       "`.ctevent list`\n"
                       "`.ctevent run <event number>`")

    @ctevent.command(name="list")
    async def list_event(self, ctx: commands.Context):
    	# Check if the bot has permission to send embeds
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            return await ctx.send("I need the 'Embed Links' permission to display this message properly.")
        try:
            info_embed = discord.Embed(
                title="CrimeTime Events!!", 
                description="An Admin-initiated Event List.", 
                color=0x00FF)
            info_embed.add_field(
                name="Events:",
                value="1  -  A heavily-crowded walkway. (Max $300)\n2  -  A broken ATM Machine. (Max $500)\n3  -  A blocked Armored Car. (Max $2000)\n \n* More will be added over time.",
                inline=False)
            await ctx.send(embed=info_embed)
        except discord.HTTPException:
            await ctx.send("An error occurred while sending the message. Please try again later.")

##########  End of Admin Commands  ##########

# Start of Leaderboard Commands
    @commands.command()  # Leaderboard Commands for Mugging
    async def muglb(self, ctx: commands.Context, stat: t.Literal["balance", "wins", "ratio"]):
        """Displays leaderboard for Player Mugging stats."""
        guildsettings = self.db.get_conf(ctx.guild)
        users: dict[int, User] = guildsettings.users

        if stat == "balance":
            sorted_users = sorted(users.items(), key=lambda x: x[1].balance, reverse=True)
            sorted_users = [i for i in sorted_users if i[1].balance]
        elif stat == "wins":
            sorted_users = sorted(users.items(), key=lambda x: x[1].p_wins, reverse=True)
            sorted_users = [i for i in sorted_users if i[1].p_wins]
        else:  # Ratio
            sorted_users = sorted(users.items(), key=lambda x: x[1].p_ratio, reverse=True)
            sorted_users = [i for i in sorted_users if i[1].p_ratio]
        
        # ⛔ Prevent IndexError if list is empty
        if not sorted_users:
            await ctx.send("No users found with any data for that stat.")
            return

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

                member = ctx.guild.get_member(user_id)
                if member:
                    username = f"{member.display_name} ({user_id})"
                else:
                    username = f"Unknown User ({user_id})"

                txt += f"{position + 1}. `{value}` : {username}\n"

            title = f"{stat.capitalize()} Leaderboard!"
            embed = discord.Embed(description=txt, title=title)
            embed.set_footer(text=f"Page {index + 1}/{pages}")
            embeds.append(embed)
            start += 15
            stop += 15

        await DynamicMenu(ctx, embeds).refresh()

############### BlackMarket Commands ###############
    @commands.group(invoke_without_command=True)
    @commands.admin_or_permissions(manage_guild=True)  # Only Admins can use this command
    async def ctbm(self, ctx: commands.Context):
        """Blackmarket code."""
        await ctx.send("Please specify a valid subcommand, e.g.:\n"
                       "`ctbm display` - Will list all items that exist.\n"
                       "`ctbm list` - Will list the three current available items to buy.\n"
                       "`ctbm buy #` - Will purchase the item if you don't already own it.\n"
                       "`ctbm sell (item you own) - Sells the item for a little less than it's worth.`"
                       )
    
    @ctbm.command(name="display")
    async def display_allitems__list(self, ctx: commands.Context):
        '''Prints out a list of all the currently created gear.'''
        member = ctx.author
        guild = ctx.guild
        guildsettings = self.db.get_conf(guild)
        user = guildsettings.get_user(member)


############### Player Equipment Commands ###############
    @commands.group(invoke_without_command=True)
    async def ctinv(self, ctx: commands.Context):
        """All commands for player interactions with gear."""
        await ctx.send("Please specify a valid subcommand, e.g.:\n"
                       "`ctinv all` - Will list a full display of your items.\n"
                       "`ctinv worn` - Will list what you are currently wearing.\n"
                       "`ctinv owned` - Items in your carried inventory.\n"
                       "`ctinv wear (item)` - Wear an item you own.\n"
                       "`ctinv remove (item)` - Remove a worn item."
                       )
    
    @ctinv.command(name="worn")
    async def display_user_worn_items(self, ctx: commands.Context):
        '''Prints out a list of all the currently worn gear.'''
        member = ctx.author
        guild = ctx.guild
        guildsettings = self.db.get_conf(guild)
        user = guildsettings.get_user(member)
        await ctx.send(f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n[**{member}**'s Worn Equipment]\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n[Weapon]          : {user.worn_weapon}\n[Head]               : {user.worn_head}\n[Chest]              : {user.worn_chest}\n[Legs]                : {user.worn_legs}\n[Feet]                : {user.worn_feet}\n[Consumable] : {user.worn_consumable}\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
    
    @ctinv.command(name="owned")
    async def display_user_owned_items(self, ctx: commands.Context):
        '''Prints out a list of all the currently worn gear.'''
        member = ctx.author
        guild = ctx.guild
        guildsettings = self.db.get_conf(guild)
        user = guildsettings.get_user(member)
        await ctx.send(f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n[**{member}**'s Inventory]\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n[Weapon]          : {user.owned_weapon}\n[Head]               : {user.owned_head}\n[Chest]              : {user.owned_chest}\n[Legs]                : {user.owned_legs}\n[Feet]                : {user.owned_feet}\n[Consumable] : {user.owned_consumable}\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
