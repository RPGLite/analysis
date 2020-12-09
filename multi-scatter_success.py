# William
# Generate scatter plots for comparison of success with possible contributing factors

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math
from bson import objectid

minor_threshold = 0.1
major_threshold = 0.33

def flip_state(s):
    return [1] + s[10:] + s[1:10]

s1data = {}
s2data = {}

for player_doc in db.players.find({"Username":{"$exists":True}, "Played":{"$gt":0}}):
    if player_doc["Username"] not in ["cptKav","probablytom"]:
        s1data[player_doc["Username"]] = {
            "played":0, "won":0, "minors":0, "majors":0, "cost":0.0
            }
        s2data[player_doc["Username"]] = {
            "played":0, "won":0, "minors":0, "majors":0, "cost":0.0
        }
        
set_config("beta")      # begin with season 1.
lookups = process_lookup("beta")    # gather s1 lookup data
for p in s1data.keys():
    costs = []
    minor_errors = []
    major_errors = []

    for g in db.completed_games.find({"usernames":p,"winner":{"$exists":True},"balance_code":{"$exists":False}}):
        if (g["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1") or 
        g["_id"] == objectid.ObjectId("5eaaee2c684de5692fc01ef6") or 
        g["_id"] == objectid.ObjectId("5ec108ef29108c1ba22cb375")):    
            # Ignore dodgy games.
            continue
    
        s1data[p]["played"] += 1                  # increment played
        if g["usernames"].index(p) == g["winner"] - 1:
            # If the player won.
            s1data[p]["won"] += 1                 # increment won
        
        pair = g["p1c1"][0] + g["p1c2"][0] if g["usernames"].index(p) == 0 else g["p2c1"][0] + g["p2c2"][0]
        if chars.index(pair[0]) > chars.index(pair[1]):
            pair = pair[1]+pair[0]          # material selection (with correct ordering) for p

        state = get_initial_state(g)        # game state
        moves = 0                           # moves made by p
        imp_moves = 0                       # moves made by p where >= 3 actions were available and the game is still 'in the balance'
        total_cost = 0.0                    # total cost of all p moves
        num_minor_errors = 0
        num_major_errors = 0

        for m in g["Moves"]:      # for every move
            if m[1] == str(g["usernames"].index(p)+1):    # if it is a move of our player.
                moves += 1              
                if count_actions_available(state, pair, lookups) > 2:   # if more than 2 actions were available
                    if m[1] == "1":     # if p is player 1
                        act, max_poss = cost(state, pair, m, lookups, classify_mistake=True)
                    else:               # if p is player 2
                        act, max_poss = cost(flip_state(state), pair, m, lookups, classify_mistake=True)
                    if max_poss > 0.1 and max_poss < 0.9:       # if the probability of P winning is between 10% and 90%
                        total_cost += ((max_poss - act) / max_poss)
                        imp_moves += 1                          # increment important moves
                        if ((max_poss - act) / max_poss) >= minor_threshold:
                            num_minor_errors += 1
                        if ((max_poss - act) / max_poss) >= major_threshold:
                            num_major_errors += 1
                        
            do_action(m, state)         # do action.

        if imp_moves > 0:
            costs += [total_cost/imp_moves]
            minor_errors += [num_minor_errors/imp_moves]
            major_errors += [num_major_errors/imp_moves]
        else:
            s1data[p]["played"] -= 1                  # decrement played
            if g["usernames"].index(p) == g["winner"] - 1:
                s1data[p]["won"] -= 1                  # decrement won
            


    s1data[p]["cost"] = np.mean(costs)
    s1data[p]["minors"] = np.mean(minor_errors)
    s1data[p]["majors"] = np.mean(major_errors)


set_config("tango-2-3") # then season 2...
lookups = process_lookup("tango-2-3")    # gather s2 lookup data
for p in s2data.keys():
    costs = []
    minor_errors = []
    major_errors = []

    for g in db.completed_games.find({"usernames":p,"winner":{"$exists":True},"balance_code":{"$exists":True}}):
        if (g["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1") or 
        g["_id"] == objectid.ObjectId("5eaaee2c684de5692fc01ef6") or 
        g["_id"] == objectid.ObjectId("5ec108ef29108c1ba22cb375")):    
            # Ignore dodgy games.
            continue
    
        s2data[p]["played"] += 1                  # increment played
        if g["usernames"].index(p) == g["winner"] - 1:
            # If the player won.
            s2data[p]["won"] += 1                 # increment won
        
        pair = g["p1c1"][0] + g["p1c2"][0] if g["usernames"].index(p) == 0 else g["p2c1"][0] + g["p2c2"][0]
        if chars.index(pair[0]) > chars.index(pair[1]):
            pair = pair[1]+pair[0]          # material selection (with correct ordering) for p

        state = get_initial_state(g)        # game state
        moves = 0                           # moves made by p
        imp_moves = 0                       # moves made by p where >= 3 actions were available and the game is still 'in the balance'
        total_cost = 0.0                    # total cost of all p moves
        num_minor_errors = 0
        num_major_errors = 0

        for m in g["Moves"]:      # for every move
            if m[1] == str(g["usernames"].index(p)+1):    # if it is a move of our player.
                moves += 1              
                if count_actions_available(state, pair, lookups) > 2:   # if more than 2 actions were available
                    if m[1] == "1":     # if p is player 1
                        act, max_poss = cost(state, pair, m, lookups, classify_mistake=True)
                    else:               # if p is player 2
                        act, max_poss = cost(flip_state(state), pair, m, lookups, classify_mistake=True)
                    if max_poss > 0.1 and max_poss < 0.9:       # if the probability of P winning is between 10% and 90%
                        total_cost += ((max_poss - act) / max_poss)
                        imp_moves += 1                          # increment important moves
                        if ((max_poss - act) / max_poss) >= minor_threshold:
                            num_minor_errors += 1
                        if ((max_poss - act) / max_poss) >= major_threshold:
                            num_major_errors += 1
                        
            do_action(m, state)         # do action.

        if imp_moves > 0:
            costs += [total_cost/imp_moves]
            minor_errors += [num_minor_errors/imp_moves]
            major_errors += [num_major_errors/imp_moves]
        else:
            s2data[p]["played"] -= 1                  # decrement played
            if g["usernames"].index(p) == g["winner"] - 1:
                s2data[p]["won"] -= 1                  # decrement won
            


    s2data[p]["cost"] = np.mean(costs)
    s2data[p]["minors"] = np.mean(minor_errors)
    s2data[p]["majors"] = np.mean(major_errors)

to_del = []
for x in s1data.keys():
    if s1data[x]["played"] >= 5:
        continue
        #print("{0}: {1}".format(x, s1data[x]))
    else:
        to_del += [x]
for e in to_del:
    s1data.pop(e)

to_del = []
for x in s2data.keys():
    if s2data[x]["played"] >= 5:
        continue
        #print("{0}: {1}".format(x, s1data[x]))
    else:
        to_del += [x]
for e in to_del:
    s2data.pop(e)



fig, axs = plt.subplots(nrows=3,ncols=2, figsize=(16,16), sharey=True)

y = [s1data[x]["won"]/s1data[x]["played"] for x in s1data.keys()]
x = [s1data[x]["cost"] for x in s1data.keys()]
s = [s1data[x]["played"] for x in s1data.keys()]

axs[0,0].set_title("SEASON 1: cost per critical move")
axs[0,0].scatter(x,y,s=s)
axs[0,0].axhline(y=0.5)
axs[0,0].axvline(x=np.mean(x))

# Do a fit.
# coefs = np.polyfit(x,y,1)
# poly = np.poly1d(coefs)
# new_x = np.linspace(min(x),max(x))
# new_y = poly(new_x)
# axs[0,0].plot(new_x, new_y)

sig_x = []
sig_y = []
for i in range(len(x)):
    if s[i] > 10:
        sig_x += [x[i]]
        sig_y += [y[i]]
coefs = np.polyfit(sig_x,sig_y,1)
poly = np.poly1d(coefs)
new_x = np.linspace(0,max(sig_x))
new_y = poly(new_x)
axs[0,0].plot(new_x, new_y)


x = [s1data[x]["minors"] for x in s1data.keys()]

axs[1,0].set_title("minor mistake per critical move ({0}% p(win) lost)".format(minor_threshold))
axs[1,0].scatter(x,y,s=s)
axs[1,0].axhline(y=0.5)
axs[1,0].axvline(x=np.mean(x))

sig_x = []
sig_y = []
for i in range(len(x)):
    if s[i] > 10:
        sig_x += [x[i]]
        sig_y += [y[i]]
coefs = np.polyfit(sig_x,sig_y,1)
poly = np.poly1d(coefs)
new_x = np.linspace(0,max(sig_x))
new_y = poly(new_x)
axs[1,0].plot(new_x, new_y)

x = [s1data[x]["majors"] for x in s1data.keys()]

axs[2,0].set_title("major mistake per critical move ({0}% p(win) lost)".format(major_threshold))
axs[2,0].scatter(x,y,s=s)
axs[2,0].axhline(y=0.5)
axs[2,0].axvline(x=np.mean(x))

sig_x = []
sig_y = []
for i in range(len(x)):
    if s[i] > 10:
        sig_x += [x[i]]
        sig_y += [y[i]]
coefs = np.polyfit(sig_x,sig_y,1)
poly = np.poly1d(coefs)
new_x = np.linspace(0,max(sig_x))
new_y = poly(new_x)
axs[2,0].plot(new_x, new_y)

# ----------

y = [s2data[x]["won"]/s2data[x]["played"] for x in s2data.keys()]
x = [s2data[x]["cost"] for x in s2data.keys()]
s = [s2data[x]["played"] for x in s2data.keys()]

axs[0,1].set_title("SEASON 2: cost per critical move")
axs[0,1].scatter(x,y,s=s)
axs[0,1].axhline(y=0.5)
axs[0,1].axvline(x=np.mean(x))

sig_x = []
sig_y = []
for i in range(len(x)):
    if s[i] > 10:
        sig_x += [x[i]]
        sig_y += [y[i]]
coefs = np.polyfit(sig_x,sig_y,1)
poly = np.poly1d(coefs)
new_x = np.linspace(0,max(sig_x))
new_y = poly(new_x)
axs[0,1].plot(new_x, new_y)

x = [s2data[x]["minors"] for x in s2data.keys()]

axs[1,1].set_title("minor mistake per critical move ({:.2f}% p(win) lost)".format(minor_threshold*100))
axs[1,1].scatter(x,y,s=s)
axs[1,1].axhline(y=0.5)
axs[1,1].axvline(x=np.mean(x))

sig_x = []
sig_y = []
for i in range(len(x)):
    if s[i] > 10:
        sig_x += [x[i]]
        sig_y += [y[i]]
coefs = np.polyfit(sig_x,sig_y,1)
poly = np.poly1d(coefs)
new_x = np.linspace(0,max(sig_x))
new_y = poly(new_x)
axs[1,1].plot(new_x, new_y)

x = [s2data[x]["majors"] for x in s2data.keys()]

axs[2,1].set_title("major mistake per critical move ({:.2f}% p(win) lost)".format(major_threshold*100))
axs[2,1].scatter(x,y,s=s)
axs[2,1].axhline(y=0.5)
axs[2,1].axvline(x=np.mean(x))

sig_x = []
sig_y = []
for i in range(len(x)):
    if s[i] > 10:
        sig_x += [x[i]]
        sig_y += [y[i]]
coefs = np.polyfit(sig_x,sig_y,1)
poly = np.poly1d(coefs)
new_x = np.linspace(0,max(sig_x))
new_y = poly(new_x)
axs[2,1].plot(new_x, new_y)

plt.tight_layout
plt.show()