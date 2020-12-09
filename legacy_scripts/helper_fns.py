# William Kavanagh, April 2020

""" Collection of helper functions for the analysis of data for the RPGLite project
"""

from pymongo import MongoClient
import numpy as np

client = MongoClient(
    "mongodb://takuu.dcs.gla.ac.uk:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
db = client.Game_data

# Order determined by lookup tables
chars = ["K", "A", "W", "R", "H", "M", "B", "G"]
pairs = []
for i in range(8):
    for j in range(i+1, 8):
        pairs += [chars[i]+chars[j]]

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

def what_config():
    if KNIGHT_ACCURACY == 60:
        return 1
    return 2 

def set_config(c):
    global KNIGHT_HEALTH, KNIGHT_DAMAGE, KNIGHT_ACCURACY, ARCHER_ACCURACY, ARCHER_DAMAGE, ARCHER_HEALTH
    global HEALER_ACCURACY, HEALER_DAMAGE, HEALER_HEAL, HEALER_HEALTH, ROGUE_ACCURACY, ROGUE_DAMAGE, ROGUE_EXECUTE, ROGUE_HEALTH
    global WIZARD_ACCURACY, WIZARD_DAMAGE, WIZARD_HEALTH, MONK_ACCURACY, MONK_DAMAGE, MONK_HEALTH
    global GUNNER_ACCURACY, GUNNER_DAMAGE, GUNNER_HEALTH, GUNNER_MISS_DAMAGE, BARBARIAN_ACCURACY, BARBARIAN_DAMAGE, BARBARIAN_RAGE_DAMAGE, BARBARIAN_HEALTH, BARBARIAN_RAGE_THRESHOLD
    if c == "beta":
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
    elif c == "tango-2-3":
        KNIGHT_HEALTH = 10
        KNIGHT_DAMAGE = 3
        KNIGHT_ACCURACY = 80

        ARCHER_HEALTH = 9
        ARCHER_DAMAGE = 2
        ARCHER_ACCURACY = 80

        HEALER_HEALTH = 9
        HEALER_DAMAGE = 2
        HEALER_ACCURACY = 90
        HEALER_HEAL = 1

        ROGUE_HEALTH = 8
        ROGUE_DAMAGE = 3
        ROGUE_ACCURACY = 70
        ROGUE_EXECUTE = 5

        WIZARD_HEALTH = 8
        WIZARD_DAMAGE = 2
        WIZARD_ACCURACY = 85

        MONK_HEALTH = 7
        MONK_DAMAGE = 1
        MONK_ACCURACY = 75

        GUNNER_HEALTH = 8
        GUNNER_DAMAGE = 4
        GUNNER_MISS_DAMAGE = 1
        GUNNER_ACCURACY = 70

        BARBARIAN_HEALTH = 9
        BARBARIAN_DAMAGE = 3
        BARBARIAN_RAGE_DAMAGE = 5
        BARBARIAN_RAGE_THRESHOLD = 4
        BARBARIAN_ACCURACY = 70
    else:
        print("Tried to set unrecognised config: " + c)

def search_opponent_pair(u1, u2):
    """
    Find number of games and average roll between two users
    
    Arguments:
        u1 {string} -- [username of player 1]
        u2 {string} -- [username of player 2]
        
    results are printed then returned:
        count {int} -- number of games between players
        u1_luck {float} -- average roll of player 1
        u2_luck {float} -- average roll of player 2
    """
    count = db.completed_games.count_documents({"usernames": [u1, u2]}) + db.completed_games.count_documents({"usernames": [u2, u1]})
    
    print("Games completed between pair:", count)
    u1_rolls = []
    u2_rolls = []
    for g in db.completed_games.find({"usernames": [u1, u2]}):
        for m in g["Moves"]:
            if m[1] == "1":
                # if it is a move our user made.
                for part in m.split("_")[1:]:
                    if "p" in part and not "skip" in part:
                        u1_rolls += [int(part.split("p")[0])]
                    elif "skip" not in part:
                        u1_rolls += [int(part)]
            else:
                for part in m.split("_")[1:]:
                    if "p" in part and not "skip" in part:
                        u2_rolls += [int(part.split("p")[0])]
                    elif "skip" not in part:
                        u2_rolls += [int(part)]
    for g in db.completed_games.find({"usernames": [u2, u1]}):
        for m in g["Moves"]:
            if m[1] == "1":
                # if it is a move our user made.
                for part in m.split("_")[1:]:
                    if "p" in part and not "skip" in part:
                        u2_rolls += [int(part.split("p")[0])]
                    elif "skip" not in part:
                        u2_rolls += [int(part)]
            else:
                for part in m.split("_")[1:]:
                    if "p" in part and not "skip" in part:
                        u1_rolls += [int(part.split("p")[0])]
                    elif "skip" not in part:
                        u1_rolls += [int(part)]

    print(u1 + " had an average roll of: " + str(np.average(u1_rolls)) + " and a std of: " + str(np.std(u1_rolls)))
    print(u2 + " had an average roll of: " + str(np.average(u2_rolls)) +
          " and a std of: " + str(np.std(u2_rolls)))
    
    return(count, np.average(u1_rolls), np.average(u1_rolls))

def full_name(i):
    if i == "K":
        return "Knight"
    if i == "A":
        return "Archer"
    if i == "H":
        return "Healer"
    if i == "R":
        return "Rogue"
    if i == "W":
        return "Wizard"
    if i == "M":
        return "Monk"
    if i == "G":
        return "Gunner"
    if i == "B":
        return "Barbarian"
    print("full name called on unrecognised letter", i)

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


def was_a_miss(action, state):
    """ Take an action string and state [], return if the action missed or not

    Arguments:
        action {string} -- full move notation
        state {string []} -- string list of state [turn, p1K, p1A, ... etc]
    """
    state_copy = list(state)
    do_action(action, state_copy)
    return state[2:] == state_copy[2:]

def do_action(action, state):
    """ Take an action string and state [], update the state

    Arguments:
        action {string} -- full move notation
        state {string []} -- string list of state [turn, p1K, p1A, ... etc]
    """

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
    Is = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17]
    for i in Is:
        state[i] = max(0, state[i])
    # Reset stun
    if action[1] == "1":
        state[9] = 0
    else:
        state[-1] = 0
    state[0] = 3 - state[0]


def do_knight_action(action, state):
    # action e.g.: p1Kp2H_41
    roll = int(action.split("_")[1])
    if roll >= 100 - KNIGHT_ACCURACY:
        if action[1] == "1":
            state[10+chars.index(action[5])] -= KNIGHT_DAMAGE
        else:
            state[1+chars.index(action[5])] -= KNIGHT_DAMAGE


def do_archer_action(action, state):
    # action e.g.: p2Ap1K_55p1R_86 OR p2Ap1K_53
    roll1 = int(action.split("_")[1].split("p")[0])
    if roll1 >= 100 - ARCHER_ACCURACY:
        if action[1] == "1":
            state[10+chars.index(action[5])] -= ARCHER_DAMAGE
        else:
            state[1+chars.index(action[5])] -= ARCHER_DAMAGE
    # If there is no second target
    if len(action.split("_")) == 2:
        return
    roll2 = int(action.split("_")[2])
    target = action.split("_")[1][-1]
    if roll2 >= 100 - ARCHER_ACCURACY:
        if action[1] == "1":
            state[10+chars.index(target)] -= ARCHER_DAMAGE
        else:
            state[1+chars.index(target)] -= ARCHER_DAMAGE


def do_healer_action(action, state):
    # action e.g.: p2Hp1Rp2H_4
    roll = int(action.split("_")[1])
    if roll >= 100 - HEALER_ACCURACY:
        if len(action.split("p")) > 3:
            if action[1] == "1":
                state[10+chars.index(action[5])] -= HEALER_DAMAGE
                state[1+chars.index(action[8])] += HEALER_HEAL
                state[1+chars.index(action[8])] = min(
                    state[1+chars.index(action[8])],
                    set_health(full_name(action[8]))
                )
            else:
                state[1+chars.index(action[5])] -= HEALER_DAMAGE
                state[10+chars.index(action[8])] += HEALER_HEAL
                state[10+chars.index(action[8])] = min(
                    state[10+chars.index(action[8])],
                    set_health(full_name(action[8]))
                )
        else:
            if action[1] == "1":
                state[10+chars.index(action[5])] -= HEALER_DAMAGE
            else:
                state[1+chars.index(action[5])] -= HEALER_DAMAGE


def do_rogue_action(action, state):
    # action e.g.: p1Rp2H_53
    roll = int(action.split("_")[1])
    if roll >= 100 - ROGUE_ACCURACY:
        if action[1] == "1":
            if state[10+chars.index(action[5])] <= ROGUE_EXECUTE:
                state[10+chars.index(action[5])] = 0
            else:
                state[10+chars.index(action[5])] -= ROGUE_DAMAGE
        else:
            if state[1+chars.index(action[5])] <= ROGUE_EXECUTE:
                state[1+chars.index(action[5])] = 0
            else:
                state[1+chars.index(action[5])] -= ROGUE_DAMAGE


def do_wizard_action(action, state):
    # action e.g.: p1Wp2W_13
    roll = int(action.split("_")[1])
    if roll >= 100 - WIZARD_ACCURACY:
        if action[1] == "1":
            state[10+chars.index(action[5])] -= WIZARD_DAMAGE
            state[18] = 1+chars.index(action[5])
        else:
            state[1+chars.index(action[5])] -= WIZARD_DAMAGE
            state[9] = 1+chars.index(action[5])


def do_monk_action(action, state):
    # etc
    roll = int(action.split("_")[1])
    if roll >= 100 - MONK_ACCURACY:
        state[0] = 3 - state[0]
        if action[1] == "1":
            state[10+chars.index(action[5])] -= MONK_DAMAGE
        else:
            state[1+chars.index(action[5])] -= MONK_DAMAGE


def do_gunner_action(action, state):
    roll = int(action.split("_")[1])
    if roll >= 100 - GUNNER_ACCURACY:
        if action[1] == "1":
            state[10+chars.index(action[5])] -= GUNNER_DAMAGE
        else:
            state[1+ chars.index(action[5])] -= GUNNER_DAMAGE
    else:
        if action[1] == "1":
            state[10+chars.index(action[5])] -= GUNNER_MISS_DAMAGE
        else:
            state[1+ chars.index(action[5])] -= GUNNER_MISS_DAMAGE


def do_barbarian_action(action, state):
    roll = int(action.split("_")[1])
    if roll >= 100 - BARBARIAN_ACCURACY:
        if action[1] == "1":
            if state[1+chars.index("B")] <= BARBARIAN_RAGE_THRESHOLD:
                state[10+chars.index(action[5])] -= BARBARIAN_RAGE_DAMAGE
            else:
                state[10+chars.index(action[5])] -= BARBARIAN_DAMAGE
        else:
            if state[10+chars.index("B")] <= BARBARIAN_RAGE_THRESHOLD:
                state[1+chars.index(action[5])] -= BARBARIAN_RAGE_DAMAGE
            else:
                state[1+chars.index(action[5])] -= BARBARIAN_DAMAGE

def find_games_with_user(u, config):
    """Return list of games in which the user played.
    
    Arguments:
        u {string} -- username
    """
    all_games = dict()
    if config == "beta":
        all_games = db.completed_games.find({"usernames": {"$exists": True}, "winner": {"$exists": True}, "balance_code": {"$exists": False}})
    elif config == "tango-2-3":
        all_games = db.completed_games.find({"usernames": {"$exists": True}, "winner": {"$exists": True}, "balance_code": "1.2"})
    else:
        print("Finding games with unknown config: " + config)
        return None
    games = []
    for g in all_games:
        if u in g["usernames"]:
            games += [g]
    return games

def get_initial_state(g):
    """Return initial [] for game state
    
    Arguments:
        g {} of game -- 
    """
    state = [int(g["Moves"][0][1])] + [0]*18    # whoever moved first won the coin toss
    for c in g["p1c1"], g["p1c2"]:
        state[chars.index(c[0]) + 1] = set_health(c)
    for c in g["p2c1"], g["p2c2"]:
        state[chars.index(c[0]) + 10] = set_health(c)
    
    return state
    
@DeprecationWarning #"This is dumb, don't use this."
def cost_raw(state, pair, notation):
    """ Returns the cost of the move taken from the state given by player 1. 
    This is done straight from file without preprocessing. Can be v expensive, use cost() having processed the lookup tables if this will be performed repeatedly.
    
    Arguments:
        state {int []} -- [state represented as list of ints]
        pair {str} -- [pair used by player one]
        move {str} -- [move taken by player one as notation]
        
    returns {float} the cost of the move made where cost = the absolute difference between the optimal probability of p(win(p1)) from the move taken and from the best move available.
    """
    
    lookup = ""
    for i in range(len(state)):
        lookup += str(state[i])
        if i < len(state)-1:
            lookup += ","

    move = ""
    for l in notation:
        if l in chars:
            move += l
        if len(move) == 1:
            move += "_"
    if len(move) > 3 and move[0] == "A":
        # rearrange archer attacks if out of order.
        if chars.index(move[2]) > chars.index(move[3]):
            move = move[:2] + move[3] + move[2]

    with open("analysis/lookupV2/"+pair.upper()+".txt", "r") as f:
        for l in f.readlines():
            if lookup in l:
                # we're on the right line...
                l = l.split(lookup+":{")[1].split("}")[0]
                m = {}
                for a in l.split(","):
                    m[a.split(":")[0]] = float(a.split(":")[1])
                return max(m.values()) - m[move]

def process_lookup(config):
    """Parses all lookup2 data into a dictionary and returns
    """
    r = {}
    print("Parsing lookups for configuration " + config + "...")
    count = 0.0
    for p in pairs:
        lookup_d = {}
        with open("analysis/lookupV2/" + config + "/action_listing/" + p + ".txt","r") as f:
            for l in f.readlines():
                moves = l.split(":{")[1].split("}")[0]
                lookup_d[l.split(":")[0]] = moves
        r[p] = lookup_d
        count += 1.0
    return r
        
def find_opt(state, pair, data):
    """
    return the best action available from the state
    """
    lookup = ""
    for i in range(len(state)):
        lookup += str(state[i])
        if i < len(state)-1:
            lookup += ","
    if lookup not in data[pair]:
        return "s"
    moves = data[pair][lookup]
    m_d = {}
    for m in moves.split(","):
        m_d[m.split(":")[0]] = float(m.split(":")[1])
    best = ""
    max_v = 0
    for m in m_d.keys():
        if m_d[m] > max_v:
            best = m
            max_v = m_d[m]
    return best

def cost(state, pair, notation, data, classify_mistake = False):
    """Finds the cost associated with a given move from a given state using supplied dictionary of all lookup values
    
    Arguments:
        state {int []} -- state modelled for p1
        pair {str} -- pair used by p1
        move {str} -- [move taken by player one unabbreviated (rolls are removed)]
        data {dict of lookups} -- [dictionary of all lookup values]
    """
    lookup = ""
    for i in range(len(state)):
        lookup += str(state[i])
        if i < len(state)-1:
            lookup += ","

    move = ""
    for l in notation:
        if l in chars:
            move += l
        if len(move) == 1:
            move += "_"
    if len(move) == 0:
        move = "skip"
    if len(move) > 3 and move[0] == "A":
        # rearrange archer attacks if out of order.
        if chars.index(move[2]) > chars.index(move[3]):
            move = move[:2] + move[3] + move[2]

    if lookup not in data[pair]:
        # POSSIBLE from unwinnable state, e.g.: low health versus gunner 
        # print("ERROR, looking for {0} in {1} dictionary".format(lookup, pair))
        if classify_mistake:
            return 0,0
        return float(0)

    moves = data[pair][lookup]
    m_d = {}
    for m in moves.split(","):
        m_d[m.split(":")[0]] = float(m.split(":")[1])

    if classify_mistake:
        if move not in m_d:
            print(move, pair, state, notation)
        return m_d[move], max(m_d.values())

    # cost = positive difference between best move and move taken
    if move in m_d.keys():
        return max(m_d.values()) - m_d[move]
    else:
        print("ERROR IN FINDING COST:")
        print(state, pair, notation)

def count_actions_available(state, pair, data):
    """
    Returns the number of moves available at a given state for specified material
    """
    lookup = ""
    for i in range(len(state)):
        lookup += str(state[i])
        if i < len(state)-1:
            lookup += ","
    #print(lookup)


    if lookup not in data[pair]:
        #print("Checking {0} with {1} -> Failed to find any actions".format(state,pair))
        return 0
    #print("Checking {0} with {1} -> Found {2} actions".format(state, pair, len(data[pair][lookup].split(","))))
    return len(data[pair][lookup].split(","))

def check_actions_available(state, pair, critical_section, data):
    """
    Returns true if the action decision is not obvious
    """
    lookup = ""
    for i in range(len(state)):
        lookup += str(state[i])
        if i < len(state)-1:
            lookup += ","

    if lookup not in data[pair]:
        return False        # Something has gone wrong / state is not winnable (low health vs G maybe?).

    actions = data[pair][lookup].split(",")
    num_actions = len(actions)

    m_d = {}
    for m in actions:
        m_d[m.split(":")[0]] = float(m.split(":")[1])
    
    #if max(m_d.values()) < critical_section or max(m_d.values()) > (1 - critical_section):
    if max(m_d.values()) < critical_section:
        return False                    # Outside of critical range

    if num_actions == 1:
        return False                    # only one action available
    
    if num_actions == 2:
        if state[16] > 0:               # Barbarians sometimes shouldn't be hit.
            return True
        elif "skip" not in actions:
            return True

    return True

def flip_state(s):
    return [1] + s[10:] + s[1:10]