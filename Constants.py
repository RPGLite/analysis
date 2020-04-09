import numpy as np

# read in the constants

KNIGHT_HEALTH = 10
KNIGHT_DAMAGE = 4
KNIGHT_ACCURACY = 60

ARCHER_HEALTH = 8
ARCHER_DAMAGE = 2
ARCHER_ACCURACY = 85

HEALER_HEALTH = 10
HEALER_DAMAGE = 2
HEALER_ACCURACY = 85
HEALER_HEAL = 1

ROGUE_HEALTH = 8
ROGUE_DAMAGE = 3
ROGUE_ACCURACY = 75
ROGUE_EXECUTE = 5

WIZARD_HEALTH = 8
WIZARD_DAMAGE = 2
WIZARD_ACCURACY = 85

MONK_HEALTH = 7
MONK_DAMAGE = 1
MONK_ACCURACY = 80

GUNNER_HEALTH = 8
GUNNER_DAMAGE = 4
GUNNER_MISS_DAMAGE = 1
GUNNER_ACCURACY = 75

BARBARIAN_HEALTH = 10
BARBARIAN_DAMAGE = 3
BARBARIAN_RAGE_DAMAGE = 5
BARBARIAN_RAGE_THRESHOLD = 4
BARBARIAN_ACCURACY = 75

def full_name(i):
    if i == "K": return "Knight"
    if i == "A": return "Archer"
    if i == "H": return "Healer"
    if i == "R": return "Rogue"
    if i == "W": return "Wizard"
    if i == "M": return "Monk"
    if i == "G": return "Gunner"
    if i == "B": return "Barbarian"
    print("full name called on unrecognised letter")

# Helper methods to build state and parse transitions
def set_health(char):
    if char == "Knight":
        return KNIGHT_HEALTH
    if char == "Archer":
        return ARCHER_HEALTH
    if char == "Healer":
        return HEALER_HEALTH
    if char == "Rogue":
        return ROGUE_HEALTH
    if char == "Wizard":
        return WIZARD_HEALTH
    if char == "Monk":
        return MONK_HEALTH
    if char == "Gunner":
        return GUNNER_HEALTH
    if char == "Barbarian":
        return BARBARIAN_HEALTH


# Take an action string and state [], update the state
def do_action(action, state):

    if action[2] == "K":
        do_knight_action(action, state)
    if action[2] == "A":
        do_archer_action(action, state)
    if action[2] == "H":
        do_healer_action(action, state)
    if action[2] == "R":
        do_rogue_action(action, state)
    if action[2] == "W":
        do_wizard_action(action, state)
    if action[2] == "M":
        do_monk_action(action, state)
    if action[2] == "G":
        do_gunner_action(action, state)
    if action[2] == "B":
        do_barbarian_action(action, state)
    # Ensure min health is 0
    Is = [0,1,2,3,4,5,6,7,9,10,11,12,13,14,15,16]
    for i in Is:
        state[i] = max(0,state[i])
    # Reset stun
    if action[1] == "1":
        state[8] = "-"
    else:
        state[17] = "-"

def do_knight_action(action, state):
    # action e.g.: p1Kp2H_41
    roll = int(action.split("_")[1])
    if roll >= 100 - KNIGHT_ACCURACY:
        if action[1] == "1":
            state[9+chars.index(action[5])] -= KNIGHT_DAMAGE
        else:
            state[chars.index(action[5])] -= KNIGHT_DAMAGE

def do_archer_action(action, state):
    # action e.g.: p2Ap1K_55p1R_86 OR p2Ap1K_53
    roll1 = int(action.split("_")[1].split("p")[0])
    if roll1 >= 100 - ARCHER_ACCURACY:
        if action[1] == "1":
            state[9+chars.index(action[5])] -= ARCHER_DAMAGE
        else:
            state[chars.index(action[5])] -= ARCHER_DAMAGE
    # If there is no second target
    if len(action.split("_")) == 2:
        return
    roll2 = int(action.split("_")[2])
    target = action.split("_")[1][-1]
    if roll2 >= 100 - ARCHER_ACCURACY:
        if action[1] == "1":
            state[9+chars.index(target)] -= ARCHER_DAMAGE
        else:
            state[chars.index(target)] -= ARCHER_DAMAGE

def do_healer_action(action, state):
    # action e.g.: p2Hp1Rp2H_4
    roll = int(action.split("_")[1])
    if roll >= 100 - HEALER_ACCURACY:
        if len(action.split("p")) > 3:
            if action[1] == "1":
                state[9+chars.index(action[5])] -= HEALER_DAMAGE
                state[chars.index(action[8])] += HEALER_HEAL
                state[chars.index(action[8])] = min(
                    state[chars.index(action[8])],
                    set_health(full_name(action[8]))
                )
            else:
                state[chars.index(action[5])] -= HEALER_DAMAGE
                state[9+chars.index(action[8])] += HEALER_HEAL
                state[9+chars.index(action[8])] = min(
                    state[9+chars.index(action[8])],
                    set_health(full_name(action[8]))
                )
        else:
            if action[1] == "1":
                state[9+chars.index(action[5])] -= HEALER_DAMAGE
            else:
                state[chars.index(action[5])] -= HEALER_DAMAGE

def do_rogue_action(action, state):
    # action e.g.: p1Rp2H_53
    roll = int(action.split("_")[1])
    if roll >= 100 - KNIGHT_ACCURACY:
        if action[1] == "1":
            if state[9+chars.index(action[5])] <= ROGUE_EXECUTE:
                state[9+chars.index(action[5])] = 0
            else:
                state[9+chars.index(action[5])] -= ROGUE_DAMAGE
        else:
            if state[chars.index(action[5])] <= ROGUE_EXECUTE:
                state[chars.index(action[5])] = 0
            else:
                state[chars.index(action[5])] -= ROGUE_DAMAGE

def do_wizard_action(action, state):
    # action e.g.: p1Wp2W_13
    roll = int(action.split("_")[1])
    if roll >= 100 - WIZARD_ACCURACY:
        if action[1] == "1":
            state[9+chars.index(action[5])] -= WIZARD_DAMAGE
            state[17] = action[5]
        else:
            state[chars.index(action[5])] -= WIZARD_DAMAGE
            state[8] = action[5]

def do_monk_action(action, state):
    # etc
    roll = int(action.split("_")[1])
    if roll >= 100 - MONK_ACCURACY:
        if action[1] == "1":
            state[9+chars.index(action[5])] -= MONK_DAMAGE
        else:
            state[chars.index(action[5])] -= MONK_DAMAGE

def do_gunner_action(action, state):
    roll = int(action.split("_")[1])
    if roll >= 100 - GUNNER_ACCURACY:
        if action[1] == "1":
            state[9+chars.index(action[5])] -= GUNNER_DAMAGE
        else:
            state[chars.index(action[5])] -= GUNNER_DAMAGE
    else:
        if action[1] == "1":
            state[9+chars.index(action[5])] -= GUNNER_MISS_DAMAGE
        else:
            state[chars.index(action[5])] -= GUNNER_MISS_DAMAGE

def do_barbarian_action(action, state):
    roll = int(action.split("_")[1])
    if roll >= 100 - BARBARIAN_ACCURACY:
        if action[1] == "1":
            if state[chars.index("B")] <= BARBARIAN_RAGE_THRESHOLD:
                state[9+chars.index(action[5])] -= BARBARIAN_RAGE_DAMAGE
            else:
                state[9+chars.index(action[5])] -= BARBARIAN_DAMAGE
        else:
            if state[9+chars.index("B")] <= BARBARIAN_RAGE_THRESHOLD:
                state[chars.index(action[5])] -= BARBARIAN_RAGE_DAMAGE
            else:
                state[chars.index(action[5])] -= BARBARIAN_DAMAGE
