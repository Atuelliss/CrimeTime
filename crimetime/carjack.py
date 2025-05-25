import discord

# This file is for the Carjacking Code of CrimeTime.
# It should contain the dictionaries of the cars and values.

# Blank Dict - { "make" : "", "year" : , "model" : "", "max" : , "value" : ,}

# Most Rare Cars:
rarest1 = { "make" : "Ferrari", "year" : 1957, "model" : "250 Testa Rossa", "max" : 22, "value" : 12100000, }
rarest2 = { "make" : "Ferrari", "year" : 1961, "model" : "GT SWB California Spyder", "max" : 50, "value" : 10900000, }
rarest3 = { "make" : "Bugatti", "year" : 1931, "model" : "Type 41 Royale Kellner", "max" : 6, "value" : 9800000,}
rarest4 = { "make" : "Ferrari", "year" : 1962, "model" : "330 TRI/LM", "max" : 1, "value" : 9300000, }
rarest5 = { "make" : "Mercedes-Benz", "year" : 1937, "model" : "540K Special Roadster", "max" : 26, "value" : 8200000, }
rarest6 = { "make" : "Bugatti", "year" : 1937, "model" : "Type 57SC Atalante", "max" : 11, "value" : 7900000, }
rarest7 = { "make" : "Mercedes-Benz", "year" : 1929, "model" : "38/250 SSK", "max" : 35, "value" : 7400000, }
rarest8 = { "make" : "Rolls-Royce", "year" : 1904, "model" : "10HP", "max" : 17, "value" : 7300000, }
rarest9 = { "make" : "Ford", "year" : 1965, "model" : "Shelby Cobra", "max" : 6, "value" : 7250000, }
rarest10 = { "make" : "Ferrari", "year" : 1962, "model" : "250 LM", "max" : 32, "value" : 6900000, }

# Semi-Rare Cars:
semirare1 = { "make" : "BMW", "year" : 1959, "model" : "507", "max" : 252, "value" : 1700000,}
semirare2 = { "make" : "Dodge", "year" : 1970, "model" : "Coronet R/T 426 Hemi Convertible", "max" : 2, "value" : 1100000,}
semirare3 = { "make" : "Lamborghini", "year" : 1974, "model" : "Countach", "max" : 2000, "value" : 964100,}
semirare4 = { "make" : "Aston Martin", "year" : 1963, "model" : "DB5", "max" : 1059, "value" : 879000,}
semirare5 = { "make" : "Ford", "year" : 1932, "model" : "T-Bucket Roadster", "max" : 12597, "value" : 221500,}
semirare6 = { "make" : "Porsche", "year" : 1965, "model" : "911", "max" : 3300, "value" : 205000,}

# Common Cars:
chevy1 = { "make" : "Chevrolet", "year" : 2004, "model" : "Corvette", "max" : 250000, "value" : 17650,}
chevy2 = { "make" : "Chevrolet", "year" : 1965, "model" : "Impala", "max" : 250000, "value" : 15041,}
chevy3 = { "make" : "Chevrolet", "year" : 2012, "model" : "Silverado", "max" : 250000, "value" : 13974,}
chevy4 = { "make" : "Chevrolet", "year" : 2022, "model" : "Tahoe", "max" : 250000, "value" : 41989,}
chevy5 = { "make" : "Chevrolet", "year" : 1973, "model" : "Nova", "max" : 250000, "value" : 10610,}

# Junk Cars:
junk1 = { "make" : "Chevrolet", "year" : 1982, "model" : "Cavalier", "max" : 250000, "value" : 1450,}
junk2 = { "make" : "Chevrolet", "year" : 2001, "model" : "Camaro", "max" : 250000, "value" : 2449,}
junk3 = { "make" : "Chevrolet", "year" : 2001, "model" : "S-10", "max" : 250000, "value" : 4989,}
junk4 = { "make" : "Chevrolet", "year" : 2016, "model" : "Malibu", "max" : 250000, "value" : 9987,}
# Groupings
rarest_cars = [rarest1, rarest2, rarest3, rarest4, rarest5, rarest6, rarest7, rarest8, rarest9, rarest10]
semi_rare_cars = [semirare1, semirare2, semirare3, semirare4, semirare5, semirare6]
common_cars = [chevy1, chevy2, chevy3, chevy4, chevy5]
junk_cars = [junk1, junk2, junk3, junk4]
all_cars = [rarest_cars, semi_rare_cars, common_cars, junk_cars]