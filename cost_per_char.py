# William Kavanagh, June 2020

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math
from bson import objectid

s1data = process_lookup("beta")
s2data = process_lookup("tango-2-3")       

def flip_state(s):
    return [1] + s[10:] + s[1:10]

char_costs = [[],[],[],[],[],[],[],[]]
missed_char_costs = [[],[],[],[],[],[],[],[]]
char_picked = [0,0,0,0,0,0,0,0]
char_moves = [0,0,0,0,0,0,0,0]
opt_char_moves_missed = [0,0,0,0,0,0,0,0]
char_won = [0,0,0,0,0,0,0,0] 


data = {}
for pair in pairs:
    data[pair] = {"s1_played":0, "s2_played":0, "s1_won":0, "s2_won":0, "s1_total_cost":0, "s2_total_cost":0}

# Process S1 games
set_config("beta")
for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":{"$exists":False}}):
    if g["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1"):    # Ignore dodgy game.
        continue
    state = get_initial_state(g)
    pair1 = g["p1c1"][0] + g["p1c2"][0]
    pair2 = g["p2c1"][0] + g["p2c2"][0]
    if chars.index(pair1[0]) > chars.index(pair1[1]):
        pair1 = pair1[1]+pair1[0]
    if chars.index(pair2[0]) > chars.index(pair2[1]):
        pair2 = pair2[1]+pair2[0]
    for p in [pair1, pair2]:
        data[p]["s1_played"] += 1       # Increment played value by 1
        for q in p:
            char_picked[chars.index(q)] += 1
    if g["winner"] == 1:
        data[pair1]["s1_won"] += 1
        for c in pair1:
            char_won[chars.index(c)] += 1
    else:
        data[pair2]["s1_won"] += 1
        for c in pair2:
            char_won[chars.index(c)] += 1
    for m in g["Moves"]:
        if m[1] == "1":
            action_cost = cost(state, pair1, m, s1data)                        
            data[pair1]["s1_total_cost"] += action_cost
            if "skip" not in m:
                char_costs[chars.index(m[2])] += [action_cost]
                char_moves[chars.index(m[2])] += 1
                if action_cost != 0:
                    opt_actor = find_opt(state, pair1, s1data)[0]
                    if opt_actor in chars:
                        opt_char_moves_missed[chars.index(opt_actor)] += 1
                        missed_char_costs[chars.index(opt_actor)] += [action_cost]
        elif m[1] == "2":
            action_cost= cost(flip_state(state), pair2, m, s1data)
            data[pair2]["s1_total_cost"] += action_cost
            if "skip" not in m:
                char_costs[chars.index(m[2])] += [action_cost]
                char_moves[chars.index(m[2])] += 1
                if action_cost != 0:
                    opt_actor = find_opt(flip_state(state), pair2, s1data)[0]
                    if opt_actor in chars:
                        opt_char_moves_missed[chars.index(opt_actor)] += 1
                        missed_char_costs[chars.index(opt_actor)] += [action_cost]

        do_action(m, state)

for c in chars:
    print("{0}: moves made {1}, average action_costof move when used: {2}, optimal moves missed: {3}, average action_costof move when missed: {4}".format(c, char_moves[chars.index(c)], np.average(char_costs[chars.index(c)]), opt_char_moves_missed[chars.index(c)], np.average(missed_char_costs[chars.index(c)])))

print()

s1char_costs = char_costs
s1missed_char_costs = missed_char_costs
s1char_moves = char_moves
s1opt_char_moves_missed = opt_char_moves_missed
s1char_picked = char_picked
s1won = char_won

char_costs = [[],[],[],[],[],[],[],[]]
missed_char_costs = [[],[],[],[],[],[],[],[]]
char_picked = [0,0,0,0,0,0,0,0] 
char_won = [0,0,0,0,0,0,0,0] 
char_moves = [0,0,0,0,0,0,0,0]
opt_char_moves_missed = [0,0,0,0,0,0,0,0]

# Process S2 games   
set_config("tango-2-3")

for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":"1.2"}):
    if g["_id"] == objectid.ObjectId("5eaaee2c684de5692fc01ef6") or g["_id"] == objectid.ObjectId("5ec108ef29108c1ba22cb375"):    # Ignore dodgy game.
        continue
    state = get_initial_state(g)
    pair1 = g["p1c1"][0] + g["p1c2"][0]
    pair2 = g["p2c1"][0] + g["p2c2"][0]
    if chars.index(pair1[0]) > chars.index(pair1[1]):
        pair1 = pair1[1]+pair1[0]
    if chars.index(pair2[0]) > chars.index(pair2[1]):
        pair2 = pair2[1]+pair2[0]
    for p in [pair1, pair2]:
        data[p]["s2_played"] += 1       # Increment played value by 1
        for q in p:
            char_picked[chars.index(q)] += 1
    if g["winner"] == 1:
        data[pair1]["s2_won"] += 1
        for c in pair1:
            char_won[chars.index(c)] += 1
    else:
        data[pair2]["s2_won"] += 1
        for c in pair2:
            char_won[chars.index(c)] += 1
    for m in g["Moves"]:
        if m[1] == "1":
            action_cost = cost(state, pair1, m, s2data)                        
            data[pair1]["s2_total_cost"] += action_cost
            if "skip" not in m:
                char_costs[chars.index(m[2])] += [action_cost]
                char_moves[chars.index(m[2])] += 1
                if action_cost != 0:
                    opt_actor = find_opt(state, pair1, s2data)[0]
                    if opt_actor in chars:
                        opt_char_moves_missed[chars.index(opt_actor)] += 1
                        missed_char_costs[chars.index(opt_actor)] += [action_cost]
        elif m[1] == "2":
            action_cost = cost(flip_state(state), pair2, m, s2data)
            data[pair2]["s2_total_cost"] += action_cost
            if "skip" not in m:
                char_costs[chars.index(m[2])] += [action_cost]
                char_moves[chars.index(m[2])] += 1
                if action_cost != 0:
                    opt_actor = find_opt(flip_state(state), pair2, s2data)[0]
                    if opt_actor in chars:
                        opt_char_moves_missed[chars.index(opt_actor)] += 1
                        missed_char_costs[chars.index(opt_actor)] += [action_cost]
        do_action(m, state)

### CHARACTER WISE

# s1char_costs = char_costs
# s1missed_char_costs = missed_char_costs
# s1char_moves = char_moves
# s1opt_char_moves_missed = opt_char_moves_missed
# s1char_picked = char_picked
# s1won = char_won

fig2, (ax1_, ax2_) = plt.subplots(nrows = 1, ncols = 2, figsize=(15,6), sharey=True)

x = [s1char_picked[i] for i in range(8)]  # pick-rate, 
y = [s1won[i]/s1char_picked[i] for i in range(8)] # win-rate
s = [np.average(s1char_costs[i]) for i in range(8)]  # error-rate
CS = ax1_.scatter(x,y,s=500, c=s, cmap="Reds", edgecolors="black")
cbar = fig2.colorbar(CS, ax=ax1_)
cbar.ax.set_ylabel('Average cost per move')
for i, txt in enumerate(chars):
    ax1_.annotate(txt, (x[i], y[i]), ha='center', color="black" if s[i] < 0.014 else "white")

x = [char_picked[i] for i in range(8)]  # pick-rate, 
y = [char_won[i]/char_picked[i] for i in range(8)] # win-rate
s = [np.average(char_costs[i]) for i in range(8)]  # error-rate
CS = ax2_.scatter(x,y,s=500, c=s, cmap="Reds", edgecolors="black")
cbar = fig2.colorbar(CS, ax=ax2_)
cbar.ax.set_ylabel('Average cost per move')
for i, txt in enumerate(chars):
    ax2_.annotate(txt, (x[i], y[i]), ha='center', color="black" if s[i] < 0.014 else "white")

ax1_.set_ylabel("Win rate")
ax1_.set_xlabel("Games played")
ax1_.set_title("Season 1")
ax2_.set_xlabel("Games played")
ax2_.set_title("Season 2")

### PAIRWISE

fig, (ax1, ax2) = plt.subplots(nrows = 1, ncols = 2, figsize=(15,6), sharey=True)

x = [data[p]["s1_played"] for p in pairs]  # pick-rate, 
y = [data[p]["s1_won"] / data[p]["s1_played"] for p in pairs] # win-rate
s = [data[p]["s1_total_cost"] / data[p]["s1_played"] for p in pairs]  # error-rate
CS = ax1.scatter(x,y,s=500, c=s, cmap="Blues", edgecolors="black")
cbar = fig.colorbar(CS, ax=ax1)
cbar.ax.set_ylabel('Average cost per game')
for i, txt in enumerate(pairs):
    ax1.annotate(txt, (x[i], y[i]), ha='center', color="black" if s[i] < 0.14 else "white")

x = [data[p]["s2_played"] for p in pairs]  # pick-rate, 
y = [data[p]["s2_won"] / data[p]["s2_played"] for p in pairs] # win-rate
s = [data[p]["s2_total_cost"] / data[p]["s2_played"] for p in pairs]  # error-rate
CS = ax2.scatter(x,y,s=500, c=s, cmap="Blues", edgecolors="black")
cbar = fig.colorbar(CS, ax=ax2)
cbar.ax.set_ylabel('Average cost per game')
for i, txt in enumerate(pairs):
    ax2.annotate(txt, (x[i], y[i]), ha='center', color="black" if s[i] < 0.14 else "white")

ax1.set_ylabel("Win rate")
ax1.set_xlabel("Games played")
ax1.set_title("Season 1")
ax2.set_xlabel("Games played")
ax2.set_title("Season 2")


plt.tight_layout()
plt.show()

# for p in data.keys():
#     print("{0}:\n\tSeason 1: Played {1}, avg. action_cost{2}\n\tSeason 2: Played {3}, avg. action_cost{4}".format(
#         p, data[p]["s1_played"], data[p]["s2_played"], data[p]["s1_total_cost"]/data[p]["s1_played"], data[p]["s2_total_cost"]/data[p]["s2_played"])
#         )

# fig, (ax2, ax3, ax4) = plt.subplots(nrows = 3, ncols = 1)

# # ind = np.arange(len(pairs))
# width = 0.35

# # for c in chars:
# #     print("{0}: moves made {1}, average action_costof move when used: {2}, optimal moves missed: {3}, average action_costof move when missed: {4}".format(c, char_moves[chars.index(c)], np.average(char_costs[chars.index(c)]), opt_char_moves_missed[chars.index(c)], np.average(missed_char_costs[chars.index(c)])))

# # rs1 = ax1.bar(ind-(width/2), [data[p]["s1_played"] for p in pairs], width, label = "season 1")
# # rs2 = ax1.bar(ind+(width/2), [data[p]["s2_played"] for p in pairs], width, label = "season 2")
# # ax1.set_ylabel("Times picked")
# # ax1.set_xticks(ind)
# # ax1.set_xticklabels(pairs)
# # ax1.legend()


# # rs1 = ax2.bar(ind-(width/2), [data[p]["s1_total_cost"]/data[p]["s1_played"] for p in pairs], width, label = "season 1")
# # rs2 = ax2.bar(ind+(width/2), [data[p]["s2_total_cost"]/data[p]["s2_played"] for p in pairs], width, label = "season 2")
# # ax2.set_ylabel("Average cost")
# # ax2.set_xticks(ind)
# # ax2.set_xticklabels(pairs)
# # ax2.legend()

# ind = np.arange(8)

# rs1 = ax2.bar(ind-(width/2), [s1char_picked[chars.index(p)] for p in chars], width, label = "season 1")
# rs2 = ax2.bar(ind+(width/2), [char_picked[chars.index(p)] for p in chars], width, label = "season 2")
# ax2.set_ylabel("Times chosen")
# ax2.set_xticks(ind)
# ax2.set_xticklabels([full_name(c) for c in chars])
# ax2.legend()



# width = 0.2

# rs1 = ax3.bar(ind-(width*1.5), [s1char_moves[c] for c in range(len(chars))], width, label = "season 1 moves made" )
# rs2 = ax3.bar(ind-(width/2), [s1opt_char_moves_missed[c] for c in range(len(chars))], width, label = "season 1 optimal moves missed" )
# rs3 = ax3.bar(ind+(width/2), [char_moves[c] for c in range(len(chars))], width, label = "season 2 moves made")
# rs4 = ax3.bar(ind+(width*1.5), [opt_char_moves_missed[c] for c in range(len(chars))], width, label = "season 2 optimal moves missed")
# ax3.set_ylabel("Moves made")
# ax3.set_xticks(ind)
# ax3.set_xticklabels([full_name(c) for c in chars])
# ax3.legend()

# rs1 = ax4.bar(ind-(width*1.5), [np.average(s1char_costs[c]) for c in range(len(chars))], width, label = "season 1 cost of actions" )
# rs2 = ax4.bar(ind-(width/2), [np.average(s1missed_char_costs[c]) for c in range(len(chars))], width, label = "season 1 cost of missed actions" )
# rs3 = ax4.bar(ind+(width/2), [np.average(char_costs[c]) for c in range(len(chars))], width, label = "season 2 cost of actions")
# rs4 = ax4.bar(ind+(width*1.5), [np.average(missed_char_costs[c]) for c in range(len(chars))], width, label = "season 2 cost of missed actions")
# ax4.set_ylabel("Average cost")
# ax4.set_xticks(ind)
# ax4.set_xticklabels([full_name(c) for c in chars])
# ax4.legend()

# plt.tight_layout()

# plt.show()