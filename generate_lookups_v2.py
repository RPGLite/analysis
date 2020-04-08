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
        possible_actions += ["A_" + target_1]
        if target_2 != "none":
            possible_actions += ["A_" + target_2]
            possible_actions += ["A_" + target_1 + target_2]
    if state[4] > 0 and state[8] != 5:  # Healer..
        for i in range(8):              # possible target
            if state[9+i] > 0:
                for j in range(8):      # possible heal target
                    if state[j] > 0:
                        possible_actions += ["H_" + chars[i] + chars[j]]
    return possible_actions

# return damage and accuracy based on action string
def find_conts(action):
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
        return HEALER_DAMAGE, HEALER_ACCURACY
    if action[0] == "B":
        return BARBARIAN_DAMAGE, BARBARIAN_ACCURACY
    if action[0] == "G":
        return BARBARIAN_DAMAGE, BARBARIAN_ACCURACY

# lookup and deal with empty values
def lookup(state):
    if state in state_probabilities.keys():
        return state_probabilities[state]
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
        if missed in state_probabilities.keys():
            print("skip:", state_probabilities[missed])
            return state_probabilities[missed]
        else:                   # p(win) = 0 is ommitted. This is possible when facing a gunner and with only 1 health remaining.
            print("skip: 0.0")
            return 0.0
    dmg, acc = find_conts(action)
    acc /= 100
    #  update damge for barbarian and rogue dependant on state.
    if action[2] <= ROGUE_EXECUTE and action[0] == "R":
        dmg = ROGUE_EXECUTE
    if state[7] < BARBARIAN_RAGE_THRESHOLD and action[0] == "B":
        dmg = BARBARIAN_RAGE_DAMAGE
    # change missed for gunner
    if action[0] == "G":
        result_state[]
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
        # N.B. not checking if health exceeds max. This will be an issue if heal increases above 1.
        result_state[chars.index(action[3])+1] = str(int(result_state[chars.index(action[3])+1]) + HEALER_HEAL)


    # State as string if action successful.
    hit = ""
    for c in result_state[:-1]:
        hit += c + ","
    hit += result_state[-1]
    result = (lookup(hit)*acc) + (lookup(missed)* (1-acc))
    # TODO: Archer with 2 additional outcomes.
    return result



chars = ["K","A","W","R","H","M","B","G"]   # Order determined by lookup tables
pairs = []
for i in range(8):
    for j in range(i+1,8):
        pairs += [chars[i]+chars[j]]

# TESTING:
pairs = ["KA"]

for p in pairs:             # for each pair..
    with open("lookupV2/all_states/" + p + ".txt", "r") as f:
        state_probabilities = process_file(f.readlines())
        with open("lookupV2/" + p + ".txt", "w") as o:
            for state in state_probabilities.keys():
                # for each state with an action decision for p1
                if state.split(",")[0] == "1" and state_probabilities[state] > 0:
                    actions_available = find_actions(state)
                    print(state)
                    for action in actions_available:
                        appraise_move(state, action)
