# William
# Generate scatter plot for all critical actions made by a single player

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math, pymongo
from bson import objectid

p = "Deanerbeck"            # CHOOSE PLAYER

fig, (ax0, ax1) = plt.subplots(ncols=2, nrows=1, figsize=(15,3), sharey=True)

lookup = process_lookup("beta")
set_config("beta")
s1_actions = []

s1_total_moves = 0

# Plot S1 games.
for g in db.completed_games.find({"usernames": p, "winner":{"$exists":True}, "balance_code":{"$exists":False}}):
    
    # ignore corrupted games
    if g["_id"] in [objectid.ObjectId("5e98b4658a225cfc82573fd1"), objectid.ObjectId("5eaaee2c684de5692fc01ef6"), objectid.ObjectId("5ec108ef29108c1ba22cb375")]:    
        continue

    pair = g["p1c1"][0] + g["p1c2"][0] if p == g["usernames"][0] else g["p2c1"][0] + g["p2c2"][0]
    if chars.index(pair[0]) > chars.index(pair[1]):
        pair = pair[1]+pair[0]
    pos = g["usernames"].index(p) + 1
    state = get_initial_state(g)

    # spin over moves
    for m in g["Moves"]:
        if m[1] == str(pos):
            s1_total_moves += 1
            if pos == 1:
                if check_actions_available(state, pair, 0.1, lookup):       # Change the 3rd value to change lower bound to define 'critical actions'
                    # actual P() and maximum possible P()
                    act, max_poss = cost(state, pair, m, lookup, classify_mistake=True)
                    s1_actions += [(max_poss - act) / max_poss]
            else:
                if check_actions_available(flip_state(state), pair, 0.1, lookup):
                    act, max_poss = cost(flip_state(state), pair, m, lookup, classify_mistake=True)
                    s1_actions += [(max_poss - act) / max_poss]
                
        do_action(m, state)

ax0.scatter([x+1 for x in range(15)], [np.average(x) for x in np.array_split(s1_actions,15)])
ax0.set_title("Season 1")
ax0.set_xlabel("Critical Action Buckets")
ax0.set_ylabel("Relative Cost")

lookup = process_lookup("tango-2-3")
set_config("tango-2-3")
s2_actions = []

s2_total_moves = 0

for g in db.completed_games.find({"usernames": p, "winner":{"$exists":True}, "balance_code":"1.2"}):
    
    # ignore corrupted games
    if g["_id"] in [objectid.ObjectId("5e98b4658a225cfc82573fd1"), objectid.ObjectId("5eaaee2c684de5692fc01ef6"), objectid.ObjectId("5ec108ef29108c1ba22cb375")]:    
        continue

    pair = g["p1c1"][0] + g["p1c2"][0] if p == g["usernames"][0] else g["p2c1"][0] + g["p2c2"][0]
    if chars.index(pair[0]) > chars.index(pair[1]):
        pair = pair[1]+pair[0]
    pos = g["usernames"].index(p) + 1
    state = get_initial_state(g)

    # spin over moves
    for m in g["Moves"]:
        if m[1] == str(pos):
            s2_total_moves += 1
            if pos == 1:
                if check_actions_available(state, pair, 0.1, lookup):       # Change the 3rd value to change lower bound to define 'critical actions'
                    # actual P() and maximum possible P()
                    act, max_poss = cost(state, pair, m, lookup, classify_mistake=True)
                    s2_actions += [(max_poss - act) / max_poss]
            else:
                if check_actions_available(flip_state(state), pair, 0.1, lookup):
                    act, max_poss = cost(flip_state(state), pair, m, lookup, classify_mistake=True)
                    s2_actions += [(max_poss - act) / max_poss]
                
        do_action(m, state)

ax1.scatter([x+1 for x in range(15)], [np.average(x) for x in np.array_split(s2_actions,15)])
ax1.set_title("Season 2")
ax1.set_xlabel("Critical Action Buckets")

print("In season 1, user {0} made {1} critical actions with an average cost of {2}. {3} were optimal ({4}), {5} actions in total".format(p, len(s1_actions), np.mean(s1_actions), s1_actions.count(0), s1_actions.count(0)/len(s1_actions), s1_total_moves))
print("In season 2, user {0} made {1} critical actions with an average cost of {2}. {3} were optimal ({4}), {5} actions in total".format(p, len(s2_actions), np.mean(s2_actions), s2_actions.count(0), s2_actions.count(0)/len(s2_actions), s2_total_moves))
plt.tight_layout()

fig2, (ax0_, ax1_) = plt.subplots(ncols=2, nrows=1, figsize=(15,6), sharey=True)

ax0_.scatter(range(len(s1_actions)), s1_actions)
ax0_.set_title("Season 1")
ax0_.set_xlabel("Critical Actions")
ax0_.set_ylabel("Relative Cost")

ax1_.scatter(range(len(s2_actions)), s2_actions)
ax1_.set_title("Season 2")
ax1_.set_xlabel("Critical Actions")
#ax1_.set_ylabel("Relative Cost")

plt.tight_layout()
#plt.savefig(r"C:\Users\bkav9\OneDrive\Pictures\figures\top_15_1d_learning.png")
plt.show()