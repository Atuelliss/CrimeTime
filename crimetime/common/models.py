import discord

from . import Base


class User(Base):
    balance:  int = 0
    p_wins:   int = 0
    p_losses: int = 0
    p_bonus:  float = 0
    r_wins:   int = 0
    r_losses: int = 0

    @property
    def p_ratio(self) -> float:
        return (self.p_wins / self.p_losses) if self.p_losses > 0 else self.p_wins
    @property
    def p_ratio_str(self) -> str:
        return f"{self.p_wins}:{self.p_losses}"

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
