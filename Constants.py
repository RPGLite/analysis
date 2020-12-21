# read in the constants

# Order determined by lookup tables
chars = ["K", "A", "W", "R", "H", "M", "B", "G"]
pairs = []
for i in range(8):
    for j in range(i+1, 8):
        pairs += [chars[i]+chars[j]]

season = 1

def change_season(newseason):
    global season
    season = newseason

    global KNIGHT_HEALTH, KNIGHT_DAMAGE, KNIGHT_ACCURACY, ARCHER_HEALTH, ARCHER_DAMAGE, ARCHER_ACCURACY, HEALER_HEALTH, HEALER_DAMAGE, HEALER_ACCURACY, HEALER_HEAL, ROGUE_HEALTH, ROGUE_DAMAGE, ROGUE_ACCURACY, ROGUE_EXECUTE, WIZARD_HEALTH, WIZARD_DAMAGE, WIZARD_ACCURACY, MONK_HEALTH, MONK_DAMAGE, MONK_ACCURACY, GUNNER_HEALTH, GUNNER_DAMAGE, GUNNER_MISS, GUNNER_ACCURACY, BARBARIAN_HEALTH, BARBARIAN_DAMAGE, BARBARIAN_RAGE, BARBARIAN_RAGE, BARBARIAN_ACCURACY

    KNIGHT_HEALTH = 10 if season == 1 else 10
    KNIGHT_DAMAGE = 4 if season == 1 else 3
    KNIGHT_ACCURACY = 60 if season == 1 else 80

    ARCHER_HEALTH = 8 if season == 1 else 9
    ARCHER_DAMAGE = 2
    ARCHER_ACCURACY = 85 if season == 1 else 80

    HEALER_HEALTH = 10 if season == 1 else 9
    HEALER_DAMAGE = 2
    HEALER_ACCURACY = 85 if season == 1 else 90
    HEALER_HEAL = 1

    ROGUE_HEALTH = 8
    ROGUE_DAMAGE = 3
    ROGUE_ACCURACY = 75 if season == 1 else 70
    ROGUE_EXECUTE = 5

    WIZARD_HEALTH = 8
    WIZARD_DAMAGE = 2
    WIZARD_ACCURACY = 85

    MONK_HEALTH = 7
    MONK_DAMAGE = 1
    MONK_ACCURACY = 80 if season == 1 else 75

    GUNNER_HEALTH = 8
    GUNNER_DAMAGE = 4
    GUNNER_MISS_DAMAGE = 1
    GUNNER_ACCURACY = 75 if season == 1 else 70

    BARBARIAN_HEALTH = 10 if season == 1 else 9
    BARBARIAN_DAMAGE = 3
    BARBARIAN_RAGE_DAMAGE = 5
    BARBARIAN_RAGE_THRESHOLD = 4
    BARBARIAN_ACCURACY = 75 if season == 1 else 70

KNIGHT_HEALTH = 10 if season == 1 else 10
KNIGHT_DAMAGE = 4 if season == 1 else 3
KNIGHT_ACCURACY = 60 if season == 1 else 80

ARCHER_HEALTH = 8 if season == 1 else 9
ARCHER_DAMAGE = 2
ARCHER_ACCURACY = 85 if season == 1 else 80

HEALER_HEALTH = 10 if season == 1 else 9
HEALER_DAMAGE = 2
HEALER_ACCURACY = 85 if season == 1 else 90
HEALER_HEAL = 1

ROGUE_HEALTH = 8
ROGUE_DAMAGE = 3
ROGUE_ACCURACY = 75 if season == 1 else 70
ROGUE_EXECUTE = 5

WIZARD_HEALTH = 8
WIZARD_DAMAGE = 2
WIZARD_ACCURACY = 85

MONK_HEALTH = 7
MONK_DAMAGE = 1
MONK_ACCURACY = 80 if season == 1 else 75

GUNNER_HEALTH = 8
GUNNER_DAMAGE = 4
GUNNER_MISS_DAMAGE = 1
GUNNER_ACCURACY = 75 if season == 1 else 70

BARBARIAN_HEALTH = 10 if season == 1 else 9
BARBARIAN_DAMAGE = 3
BARBARIAN_RAGE_DAMAGE = 5
BARBARIAN_RAGE_THRESHOLD = 4
BARBARIAN_ACCURACY = 75 if season == 1 else 70