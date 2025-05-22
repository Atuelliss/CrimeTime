import discord

from . import Base
from .. import blackmarket

class User(Base):
    '''Stored User Info'''
    balance: int = 0     #Cash Balance
    gold_bars: int = 0   #Gold Bars Owned
    gems_owned: int = 0  #Gems Owned
    p_wins:   int = 0    #Player Mugging Wins
    p_losses: int = 0    #Player Mugging Losses
    p_bonus:  float = 0  #Player Bonus from Win/Loss Ratio
    pve_win: int = 0     #Basic "Mug" win count.
    pve_loss: int = 0    #Basic "Mug" loss count.
    r_wins:   int = 0    #Player Robbery Wins - Upcoming
    r_losses: int = 0    #Player Robbery Losses - Upcoming
    h_wins:   int = 0    #Player Heist Wins - Upcoming
    h_losses: int = 0    #Player Heist Losses - Upcoming
    pop_up_wins: int = 0 #Player Pop-up Challenge victories - upcoming.
    pop_up_losses: int = 0 #Player Pop-up Challenge losses - upcoming.
    mugclear_count: int = 0   #Number of times Player has used "clearratio"
    player_exp: int = 0   #Total player experience.
    player_level: int = 0 #Future variable for Player level.
    tnl_exp: int = 0 #Exp needed for next level.
    recent_targets: list[int] = []

    # Player worn Inventory bits
    worn_weapon: str | None = None
    worn_head: str | None = None
    worn_chest: str | None = None
    worn_legs: str | None = None
    worn_feet: str | None = None
    worn_consumable: str | None = None
    player_atk_bonus: int = 0
    player_def_bonus: int = 0

    # Player inventory storage bits
    owned_weapon: dict[str, int] = {}
    owned_head: dict[str, int] = {}
    owned_chest: dict[str, int] = {}
    owned_legs: dict[str, int] = {}
    owned_feet: dict[str, int] = {}
    owned_consumable: dict[str, int] = {}

    # Ratio property sets
    @property # Ratio for player pvp mugging stats
    def p_ratio(self) -> float:
        return round((self.p_wins / self.p_losses) if self.p_losses > 0 else self.p_wins, 2)
    @property
    def p_ratio_str(self) -> str:
        return f"{self.p_wins}:{self.p_losses}"
    @property # Ratio for Player Robbery stats
    def r_ratio(self) -> float:
        return (self.r_wins / self.r_losses) if self.r_losses > 0 else self.r_wins
    @property
    def r_ratio_str(self) -> str:
        return f"{self.r_wins}:{self.r_losses}"
    @property # Ratio for Player Heist stats
    def h_ratio(self) -> float:
        return (self.h_wins / self.h_losses) if self.h_losses > 0 else self.h_wins
    @property
    def h_ratio_str(self) -> str:
        return f"{self.h_wins}:{self.h_losses}"    
    @property  # Ratio for random pop-up mugging challenges
    def pop_up_ratio(self) -> float:
        return (self.pop_up_wins / self.pop_up_losses) if self.pop_up_losses > 0 else self.pop_up_wins    
    @property
    def pop_up_ratio_str(self) -> str:
        return f"{self.pop_up_wins}:{self.pop_up_losses}"
    @property
    def total_pve_mug(self) -> str:
        return f"{self.pve_win}:{self.pve_loss}"
#        return f"{self.mug_pve_win_count}:{self.mug_pve_loss_count}"

    #Update the Users atk bonus above when wearing a weapon.
    @property
    def player_atk_bonus(self) -> float:
        if not self.worn_weapon:
            return 0
        for item in blackmarket.all_items:
            if item["keyword"] == self.worn_weapon:
                return item.get("factor", 0)
        return 0

    #Update the Users def bonus above when wearing armor.
    @property
    def player_def_bonus(self) -> float:
        """Calculate total defense bonus from equipped armor (head, chest, legs, feet)."""
        total = 0.0
        worn_slots = [
            self.worn_head,
            self.worn_chest,
            self.worn_legs,
            self.worn_feet,
        ]
        for keyword in worn_slots:
            if not keyword:
                continue
            for item in blackmarket.all_items:
                if item["keyword"] == keyword:
                    total += item.get("factor", 0)
                    break
        return round(total, 4)  # Rounded for display or comparison

class GuildSettings(Base):
    users: dict[int, User] = {}

    def get_user(self, user: discord.User | int) -> User:
        uid = user if isinstance(user, int) else user.id
        return self.users.setdefault(uid, User())

class DB(Base):
    configs: dict[int, GuildSettings] = {}

    def get_conf(self, guild: discord.Guild | int) -> GuildSettings:
        gid = guild if isinstance(guild, int) else guild.id
        return self.configs.setdefault(gid, GuildSettings())