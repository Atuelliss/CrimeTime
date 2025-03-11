import discord

from . import Base

class BlackMarketData(Base):
    '''Stored Item Info'''
    item_name: dict = {}
    wear_loc: int = 0  #Need to define the wear_loc as 1-Head, 2-Chest, 3-Legs, 4-Feet, 5-Weapon
    tier: int = 0  #What tier of item it is. Represented 1-5. (Common, Uncommon, Rare, Military, Raid)
    item_cost: int = 0 #Cost of the item itself.
    item_factor_value: float = 0 #Impact on pvp-mugging attack/defense.

#Item list, contains Name, Keyword, Wear_loc, Tier, Cost, Factor Value,
# {"name": , "keyword": , "wear": , "tier": , "cost": , "factor": }


########## Tier 1 Items ##########
#Head-Worn Items
black_bandana = {"name": "a black bandana", "keyword": "bandana", "wear": 1, "tier": 1, "cost": 3000, "factor": 0.01}
baseball_cap =  {"name": "a baseball cap", "keyword": "cap","wear": 1, "tier": 1, "cost": 3000, "factor": 0.01}
fez =           {"name": "a small red fez", "keyword": "fez","wear": 1, "tier": 1, "cost": 3000, "factor": 0.01}
sunglasses =    {"name": "a pair of reflective sunglasses", "keyword": "sunglasses","wear": 1, "tier": 1, "cost": 4500, "factor": 0.02}
fedora =        {"name": "a black felt fedora", "keyword": "fedora","wear": 1, "tier": 1, "cost": 4500, "factor": 0.02}
#Chest-Worn Items
flanel_shirt =   {"name": "a checkered flanel shirt", "keyword": "shirt","wear": 2, "tier": 1, "cost": 3000, "factor": 0.01}
safety_vest =    {"name": "a bright yellow safety vest", "keyword": "vest","wear": 2, "tier": 1, "cost": 3000, "factor": 0.01}
sports_bra =     {"name": "a Calia-brand black sports bra", "keyword": "bra","wear": 2, "tier": 1, "cost": 3000, "factor": 0.01}
midrift_tshirt = {"name": "a tie-dye midrift t-shirt", "keyword": "shirt","wear": 2, "tier": 1, "cost": 4500, "factor": 0.02}
leather_biker_cut = {"name": "a black leather biker's cut", "keyword": "cut","wear": 2, "tier": 1, "cost": 4500, "factor": 0.02}
#Leg-Worn Items
running_shorts = {"name": "a pair of thin running shorts", "keyword": "shorts","wear": 3, "tier": 1, "cost": 3000, "factor": 0.01}
mini_skirt =     {"name": "a tight black mini-skirt", "keyword": "skirt","wear": 3, "tier": 1, "cost": 3000, "factor": 0.01}
boxer_shorts =   {"name": "a pair of SpongeBob boxer shorts", "keyword": "shorts","wear": 3, "tier": 1, "cost": 3000, "factor": 0.01}
denim_jeans =    {"name": "a pair faded blue denim jeans", "keyword": "jeans", "wear": 3, "tier": 1, "cost": 4500, "factor": 0.02}
black_slacks =   {"name": "a pair of black business slacks", "keyword": "slacks","wear": 3, "tier": 1, "cost": 4500, "factor": 0.02}
#Foot-Worn Items
flip_flops =      {"name": "a pair sea-green flip-flops", "keyword": "flip-flops","wear": 4, "tier": 1, "cost": 3000, "factor": 0.01}
high_heels =      {"name": "a pair red stiletto high heels", "keyword": "heels","wear": 4, "tier": 1, "cost": 3000, "factor": 0.01}
ballet_slippers = {"name": "a pair of flimsy white ballet slippers", "keyword": "slippers","wear": 4, "tier": 1, "cost": 3000, "factor": 0.01}
tennis_shoes =    {"name": "a pair black Converse tennis shoes", "keyword": "shoes","wear": 4, "tier": 1, "cost": 4500, "factor": 0.02}
work_boots =      {"name": "a pair Timberland work boots", "keyword": "boots","wear": 4, "tier": 1, "cost": 4500, "factor": 0.02}
#Weapon-Slot Items
small_rock =     {"name": "a small smooth-faced rock", "keyword": "rock","wear": 5, "tier": 1, "cost": 5000, "factor": 0.01}
wood_stick =     {"name": "a small pointy wood stick", "keyword": "stick","wear": 5, "tier": 1, "cost": 5000, "factor": 0.01}
leather_gloves = {"name": "a pair of fingerless black leather gloves", "keyword": "gloves","wear": 5, "tier": 1, "cost": 5000, "factor": 0.01}
wood_club =      {"name": "a small wooden club", "keyword": "club","wear": 5, "tier": 1, "cost": 7500, "factor": 0.02}
brass_knuckles = {"name": "a set of dull brass knuckles", "keyword": "knuckles","wear": 5, "tier": 1, "cost": 7500, "factor": 0.02}

########## Tier 2 Items ##########
#Head-Worn Items
football_helmet = {"name": "a football helmet", "keyword": "helmet","wear": 1, "tier": 2, "cost": 6500, "factor": 0.02}
hard_hat =        {}
plastic_beerhat = {}
ski_mask =        {}
old_war_helmet1 = {"name": "a WWII OD-Green Helmet", "keyword": "helmet1","wear": 1, "tier": 2, "cost": 8500, "factor": 0.03}
#Chest-Worn Items
padded_jacket =     {}
zip_up_hoodie =     {}
ugly_xmas_sweater = {}
satin_blaiser =     {}

#Leg-Worn Items
cargo_pants1 = {"name": "a pair of black cargo pants", "keyword": "pants","wear": 3, "tier": 2, "cost": 8500, "factor": 0.03}
#Foot-Worn Items
combat_boots1 = {}

########## Tier 3 Items ##########
police_helmet = {}
riot_helmet = {}
flak_helmet = {}

##### Assigning Tier-1 Items into a grouping #####
tier_1_head = [black_bandana, baseball_cap, fez, sunglasses, fedora]
tier_1_chest = [flanel_shirt, safety_vest, sports_bra, midrift_tshirt, leather_biker_cut]
tier_1_legs = [running_shorts, mini_skirt, boxer_shorts, denim_jeans, black_slacks]
tier_1_feet = [flip_flops, high_heels, ballet_slippers, tennis_shoes, work_boots]
tier_1_weapon = [small_rock, wood_stick, leather_gloves, wood_club, brass_knuckles]
# Put the groups into one List of all Tier-1 items.
tier_1_grouping = [tier_1_legs, tier_1_chest, tier_1_legs, tier_1_feet, tier_1_weapon]