import discord
from redbot.core import commands

async def update_pbonus(cog, ctx: commands.Context, member: discord.Member) -> None:
    """Recalculate and update a user's P-bonus based on their win/loss ratio."""
    guildsettings = cog.db.get_conf(ctx.guild)
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
    cog.save()
    