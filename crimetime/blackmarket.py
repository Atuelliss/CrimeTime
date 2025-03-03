import discord

from . import Base

class BlackMarketData(Base):
    '''Stored Item Info'''
    item_name: dict = {}
    wear_loc: int = 0  #Need to define the wear_loc as 1-Head, 2-Chest, 3-Legs, 4-Feet, 5-Weapon
    tier: int = 0  #What tier of item it is. Represented 1-5. (Common, Uncommon, Rare, Military, Raid)
    item_cost: int = 0 #Cost of the item itself.
    item_factor_value: float = 0 #Impact on pvp-mugging attack/defense.

#Item list, contains Name, Wear_loc, Tier, Cost, Factor Value,
# {"name": , "wear": , "tier": , "cost": , "factor": }

#Head Worn Items
black_bandana = {"name": "Black Bandana", "wear": 1, "tier": 1, "cost": 300, "factor": 0.01}
baseball_cap = {"name": "Ball Cap", "wear": 1, "tier": 1, "cost": 500, "factor": 0.02}
football_helmet = {}
sunglasses = {}
old_war_helmet1 = {}
old_war_helmet2 = {}
police_helmet = {}
riot_helmet = {}
flak_helmet = {}
