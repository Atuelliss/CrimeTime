import discord
from redbot.core import commands, Config
import random
from typing import Optional

class Mug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)

        # Default user data
        default_user = {
            "balance": 0,  
            "wins": 0,    
            "losses": 0    
        }
        self.config.register_user(**default_user)

    # Separate cooldown for mugging a stranger (no target)
    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.user)  # cooldown for mugging no target
    async def mug(self, ctx, target: Optional[discord.Member] = None):
        author = ctx.author
        strangers = ["a smart-mouthed boy", "a grouchy old man", "an elderly woman", 
                    "a sweet foreign couple", "a man in a business suit", "a doped-out gang-banger", 
                    "an off-duty policeman", "a local politician", "a lady-of-the-night", 
                    "a random stranger", "a stuffy-looking banker", "a creepy little girl", "a sad-faced clown",
                    "a Dwarf in a penguin costume", "a sleep-deprived college Student", 
                    "Elon Musk!!", "Bill Clinton!!", "Vladamir Putin!!", "a scruffy Puppy with a wallet in it's mouth",
                    "a hyper Ballerina", "a boy dressed as a Stormtrooper", "a girl dressed as Princess Leia",
                    "Bigfoot!!", "a baby in a stroller", "Steve Job's corpse", "Rosanne Barr", "another mugger bad the job",
                    "a man in a transparent banana costume", "Borat!!", "a group of drunk frat boys", "a poor girl doing the morning walk of shame"]
        if target is None or target == author:  # No target or self-mugging
            success = random.choice([True, True, False])
            if success:
                reward = random.randint(1, 25)
                await self.update_balance(author, reward)
                await ctx.send(f"**{author.display_name}** successfully mugged *{random.choice(strangers)}* and made off with ${reward}!")
            else:
                await ctx.send(f"**{author.display_name}** looked around for someone to mug but found no one nearby...")
        else:
            # Separate cooldown for mugging another user
            await self.handle_mug_against_user(ctx, author, target)

    # Handle mugging against another user
    @commands.cooldown(1, 0, commands.BucketType.user)  # cooldown for mugging another user
    async def handle_mug_against_user(self, ctx, author, target):
        if target.bot:
            await ctx.send("You cannot mug bots!")
            return

        # Fetch user data
        author_data = await self.config.user(author).all()
        target_data = await self.config.user(target).all()

        # Check if the target's balance is less than $35
        if target_data["balance"] < 35:
            await ctx.send(f"The target has less than $35 and isn't worth mugging.")
            return

        # Calculate difficulty based on target's win/loss ratio
        difficulty = self.calculate_difficulty(target_data)

        success_chance = random.uniform(0, 1)
        if success_chance > difficulty:
            mug_amount = min(int(target_data["balance"] * 0.03), 1000)
            if mug_amount > 0:
                await self.update_balance(author, mug_amount)
                await self.update_balance(target, -mug_amount)
                await self.update_wins_losses(author, success=True)
                await ctx.send(f"**{author.display_name}** successfully mugged **{target.display_name}** for ${mug_amount}!")
            else:
                await ctx.send(f"**{target.display_name}** doesn't have enough money to steal!")
        else:
            await self.update_wins_losses(author, success=False)
            await ctx.send(f"**{author.display_name}** failed to mug **{target.display_name}** and ran away empty-handed.")

    # Check balance and stats
    @commands.command()
    async def mugcheck(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        data = await self.config.user(member).all()
        wins = data["wins"]
        losses = data["losses"]
        balance = data["balance"]
        ratio = f"{wins}:{losses}"

        await ctx.send(f"**{member.display_name}**\nBalance: ${balance}\nWin/Loss Ratio: {ratio}")

    # Admin command to reset a user's info (admins can use this)
    @commands.command()
    @commands.has_permissions(administrator=True)  # Admins can use this command
    async def mugclearbal(self, ctx, member: discord.Member):
        """Reset a user's stats balance to 0."""
        await self.config.user(member).balance.set(0)     
        await ctx.send(f"**{member.display_name}**'s Balance have been reset to 0.")

    @commands.command()
    @commands.has_permissions(administrator=True)  # Admins can use this command
    async def mugclearrat(self, ctx, member: discord.Member):
        '''Reset users Wins and Losses to 0'''
        await self.config.user(member).wins.set(0)
        await self.config.user(member).losses.set(0)
        await ctx.send(f"**{member.display_name}**'s Wins/Losses have been reset to 0.")

    # Helper function to update balance
    async def update_balance(self, user, amount: int):
        current_balance = await self.config.user(user).balance()
        await self.config.user(user).balance.set(current_balance + amount)

    # Helper function to update win/loss record
    async def update_wins_losses(self, user, success: bool):
        if success:
            wins = await self.config.user(user).wins()
            await self.config.user(user).wins.set(wins + 1)
        else:
            losses = await self.config.user(user).losses()
            await self.config.user(user).losses.set(losses + 1)

    # Difficulty calculation based on win/loss ratio
    def calculate_difficulty(self, target_data):
        wins = target_data["wins"]
        losses = target_data["losses"]
        if losses == 0:
            return 0.7  
        return min(1.0, (wins / (wins + losses))) 

# Red Bot Setup
async def setup(bot):
    cog = Mug(bot)
    await bot.add_cog(cog)
