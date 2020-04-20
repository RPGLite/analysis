# William Kavanagh
# April 2020
# Parse the files in lookupV2/all_states/* !ignore _README.txt into a more usable form.

# Have some constants...

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

# For every pair in RPGLite generate a lookup table of the following form:
# [state_from_with_action_choice_for_pair] : {action_0: p(win), action_1: p(win), ...}

# Example PRISM output.
# 154598:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,0,0,10,0,0)=0.33796182254127316
# 154599:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,0,1,0,0,0)=0.6523495521998637
# 154600:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,0,3,0,0,0)=0.5184244285351762
# 154601:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,0,5,0,0,0)=0.40691725228836945
# 154602:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,0,7,0,0,0)=0.3093155328211462
# 154603:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,2,0,0,0,0)=0.7431252835718589
# 154604:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,4,0,0,0,0)=0.6212796524027482
# 154605:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,6,0,0,0,0)=0.5475144896852222
# 154606:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,8,0,0,0,0)=0.43906510435548624
# 154607:(2,10,8,0,0,0,0,0,0,0,10,0,0,0,10,0,0,0,0)=0.3318617957490307

# For each pair:
    # generate dictionary of state (as string) paired with p(win)
    # create file
    # for each state:
        # if the state has an action decision for P1:
            # generate list of possible actions:
            # calculate probability of winning having performed those actions (sum of outcomes * their probability)
            # print to file

# Take a file from lookupV2 and return a dictionary of results.
# form: {<state_as_csv_string>:p(win)}
def process_file(lines):
    ret_dict = {}
    for l in lines:
        ret_dict[l.split("(")[1].split(")")[0]] = float(l.split("=")[1])
    return ret_dict

# take a state as a string, return a list of possible actions e.g. ["skip", "K_K", "K_A", "A_KA", "A_K", "A_A"]
def find_actions(state):
    global chars
    possible_actions = ["skip"]
    state = state.split(",")[1:]        # We already know state[0] is 1 so remove it.
    for i in range(len(state)):
        state[i] = int(state[i])
    for c in [0,2,3,5,6,7]:             # 6 chars have simple notation.
        if state[c] > 0 and state[8] != c+1:  # if the char can act.
            for i in range(8):                  # for every character
                if state[9+i] > 0:                  # if they are alive on the opponent team
                    possible_actions += [chars[c] + "_" + chars[i]]   # the knight can hit them
    if state[1] > 0 and state[8] != 2:  # Archer..
        target_1 = "none"
        target_2 = "none"
        for i in range(8):
            if state[9+i] > 0:
                if target_1 == "none":
                    target_1 = chars[i]
                else:
                    target_2 = chars[i]
        if target_1 != "none":
            possible_actions += ["A_" + target_1]
        if target_2 != "none":
            possible_actions += ["A_" + target_2]
            possible_actions += ["A_" + target_1 + target_2]
    if state[4] > 0 and state[8] != 5:  # Healer..
        for i in range(8):              # possible target
            if state[9+i] > 0:
                heal_targets = []
                for j in range(8):      # possible heal target
                    if state[j] > 0 and state[j] < max_health(chars[j]):
                        heal_targets += [chars[j]]
                if len(heal_targets) > 0:
                    for t in heal_targets:
                        possible_actions += ["H_" + chars[i] + t]
                else:
                    possible_actions += ["H_" + chars[i]]
    return possible_actions

# return damage and accuracy based on action string
def find_constants(action):
    if action[0] == "K":
        return KNIGHT_DAMAGE, KNIGHT_ACCURACY
    if action[0] == "A":
        return ARCHER_DAMAGE, ARCHER_ACCURACY
    if action[0] == "W":
        return WIZARD_DAMAGE, WIZARD_ACCURACY
    if action[0] == "R":
        return ROGUE_DAMAGE, ROGUE_ACCURACY
    if action[0] == "H":
        return HEALER_DAMAGE, HEALER_ACCURACY
    if action[0] == "M":
        return MONK_DAMAGE, MONK_ACCURACY
    if action[0] == "B":
        return BARBARIAN_DAMAGE, BARBARIAN_ACCURACY
    if action[0] == "G":
        return GUNNER_DAMAGE, GUNNER_ACCURACY

def max_health(c):
    if c == "K": return KNIGHT_HEALTH
    if c == "A": return ARCHER_HEALTH
    if c == "W": return ARCHER_HEALTH
    if c == "R": return ROGUE_HEALTH
    if c == "H": return HEALER_HEALTH
    if c == "M": return MONK_HEALTH
    if c == "B": return BARBARIAN_HEALTH
    if c == "G": return GUNNER_HEALTH

# lookup and deal with empty values
def lookup(state):
    if state in state_probabilities.keys():
        return round(state_probabilities[state],5)
    return 0.0

# take a state (string []) and an action (string). Return the probability of winning should that action be taken.
def appraise_move(state, action):
    # Let's get a string representation of missing, we'll called it missed.
    result_state = state.split(",")
    result_state[0] = "2"     # flip turn
    result_state[9] = "0"     # reset stuns
    missed = ""
    for c in result_state[:-1]:
        missed += c + ","
    missed += result_state[-1]
    if action == "skip":        # Skip is easy, 1 * p(win) having missed.
        return lookup(missed)
    dmg, acc = find_constants(action)
    acc /= 100
    #  update damage for barbarian and rogue dependant on state.
    if int(result_state[10+chars.index(action[2])]) <= ROGUE_EXECUTE and action[0] == "R":
        dmg = ROGUE_EXECUTE
    if int(result_state[7]) <= BARBARIAN_RAGE_THRESHOLD and action[0] == "B":
        dmg = BARBARIAN_RAGE_DAMAGE
    # change missed for gunner
    if action[0] == "G":
        result_state[chars.index(action[2]) + 10] = \
            str(max(0,int( result_state[chars.index(action[2]) + 10]) - GUNNER_MISS_DAMAGE))
        missed = ""
        for c in result_state[:-1]:
            missed += c + ","
        missed += result_state[-1]
        dmg -= GUNNER_MISS_DAMAGE   # tidy up after ourselves so we don't do miss damage twice.
    result_state[chars.index(action[2]) + 10] = \
        str(max(0,int( result_state[chars.index(action[2]) + 10]) - dmg))
    # flip turn again for monk.
    if action[0] == "M":
        result_state[0] = "1"
    # stun for wizard
    if action[0] == "W":
        result_state[-1] = str(chars.index(action[2]) + 1)
    # heal for healer
    if action[0] == "H" and len(action) > 3:
        # N.B. not checking if health exceeds max. This wil be an issue if heal increases above 1.
        result_state[chars.index(action[3])+1] = str(int(result_state[chars.index(action[3])+1]) + HEALER_HEAL)

    # State as string if action successful.
    hit = ""
    for c in result_state[:-1]:
        hit += c + ","
    hit += result_state[-1]
    result = (lookup(hit)*acc) + (lookup(missed)* (1-acc))
    # Archer with 2 additional outcomes.
    if action[0] == "A" and len(action) > 3:
        hit_1 = hit
        result_state = state.split(",")
        result_state[0] = "2"
        result_state[9] = "0"
        # hit second char.
        result_state[chars.index(action[3]) + 10] = \
            str(max(0,int( result_state[chars.index(action[3]) + 10]) - dmg))
        hit_2 = ""
        for c in result_state[:-1]:
            hit_2 += c + ","
        hit_2 += result_state[-1]
        # hit first char again
        result_state[chars.index(action[2]) + 10] = \
            str(max(0,int( result_state[chars.index(action[2]) + 10]) - dmg))
        hit_both = ""
        for c in result_state[:-1]:
            hit_both += c + ","
        hit_both += result_state[-1]
        # redo result calc.
        result = (acc*acc*lookup(hit_both)) + (acc*(1-acc)*lookup(hit_1)) + \
            (acc*(1-acc)*lookup(hit_2)) + ((1-acc)*(1-acc)*lookup(missed))
    return round(result,5)

chars = ["K","A","W","R","H","M","B","G"]   # Order determined by lookup tables
pairs = []
for i in range(8):
    for j in range(i+1,8):
        pairs += [chars[i]+chars[j]]

for p in pairs:             # for each pair..
    with open("lookupV2/all_states/" + p + ".txt", "r") as f:
        state_probabilities = process_file(f.readlines())
        with open("lookupV2/" + p + ".txt", "w") as o:
            for state in state_probabilities.keys():
                # for each state with an action decision for p1
                if state.split(",")[0] == "1" and state_probabilities[state] > 0:
                    actions_available = find_actions(state)
                    o.write(state + ":{")
                    for i in range(len(actions_available)):
                        r = appraise_move(state, actions_available[i])
                        o.write(actions_available[i] + ":" + str(r))
                        if i < len(actions_available) - 1:
                            o.write(",")
                        else:
                            o.write("}\n")
    print(p, "done.")
