# Who is the best player? Can we find out? Let's try.
# Sept 2020

import pymongo
from bson import objectid
from helper_fns import *
import matplotlib.pyplot as plt
import numpy as np

# What are the average costs used in either season by all pairs.
s1_data = process_lookup("beta")
set_config("beta")
s1_averages = {p:{} for p in pairs} 
for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":{"$exists":False}}):
    
    # Ignore dodgy game.
    if g["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1") or g["_id"] == objectid.ObjectId("5eaaee2c684de5692fc01ef6") or g["_id"] == objectid.ObjectId("5ec108ef29108c1ba22cb375"):    # Ignore dodgy game.
        continue

    # Get pairs
    state = get_initial_state(g)
    pair1 = g["p1c1"][0] + g["p1c2"][0]
    pair2 = g["p2c1"][0] + g["p2c2"][0]
    if chars.index(pair1[0]) > chars.index(pair1[1]):
        pair1 = pair1[1]+pair1[0]
    if chars.index(pair2[0]) > chars.index(pair2[1]):
        pair2 = pair2[1]+pair2[0]

    # process moves
    for m in g["Moves"]:
        if m[1] == "1":                        
            c = cost(state, pair1, m, s1_data)
            if str(state) in s1_averages[pair1]:
                s1_averages[pair1][str(state)] += [c]
            else: 
                s1_averages[pair1][str(state)] = [c]
        elif m[1] == "2":
            c = cost(flip_state(state), pair2, m, s1_data)
            if str(flip_state(state)) in s1_averages[pair2]:
                s1_averages[pair2][str(flip_state(state))] += [c]
            else: 
                s1_averages[pair2][str(flip_state(state))] = [c]
        do_action(m, state)

s2_data = process_lookup("tango-2-3")
set_config("tango-2-3")
s2_averages = {p:{} for p in pairs} 
for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":"1.2"}):
    
    # Ignore dodgy game.
    if g["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1") or g["_id"] == objectid.ObjectId("5eaaee2c684de5692fc01ef6") or g["_id"] == objectid.ObjectId("5ec108ef29108c1ba22cb375"):    # Ignore dodgy game.
        continue

    # Get pairs
    state = get_initial_state(g)
    pair1 = g["p1c1"][0] + g["p1c2"][0]
    pair2 = g["p2c1"][0] + g["p2c2"][0]
    if chars.index(pair1[0]) > chars.index(pair1[1]):
        pair1 = pair1[1]+pair1[0]
    if chars.index(pair2[0]) > chars.index(pair2[1]):
        pair2 = pair2[1]+pair2[0]

    # process moves
    for m in g["Moves"]:
        if m[1] == "1":                        
            c = cost(state, pair1, m, s2_data)
            if str(state) in s2_averages[pair1]:
                s2_averages[pair1][str(state)] += [c]
            else: 
                s2_averages[pair1][str(state)] = [c]
        elif m[1] == "2":
            c = cost(flip_state(state), pair2, m, s2_data)
            if str(flip_state(state)) in s2_averages[pair2]:
                s2_averages[pair2][str(flip_state(state))] += [c]
            else: 
                s2_averages[pair2][str(flip_state(state))] = [c]
        do_action(m, state)

def find_deviance(player_name):
    
    deviance = 0.0
    moves_made = 0
    
    for g in db.completed_games.find({"winner":{"$exists":True}, "usernames":player_name}):
        
        # Ignore dodgy game.
        if g["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1") or g["_id"] == objectid.ObjectId("5eaaee2c684de5692fc01ef6") or g["_id"] == objectid.ObjectId("5ec108ef29108c1ba22cb375"):    # Ignore dodgy game.
            continue

        # configure for season.
        data = s1_data
        comp_data = s1_averages
        if "balance_code" in g:
            set_config("tango-2-3")
            data = s2_data
            comp_data = s2_averages
        else:
            set_config("beta")

        # Get pairs
        state = get_initial_state(g)
        pair1 = g["p1c1"][0] + g["p1c2"][0]
        pair2 = g["p2c1"][0] + g["p2c2"][0]
        if chars.index(pair1[0]) > chars.index(pair1[1]):
            pair1 = pair1[1]+pair1[0]
        if chars.index(pair2[0]) > chars.index(pair2[1]):
            pair2 = pair2[1]+pair2[0]
        
        if g["usernames"][0] == player_name:
            user_pair = pair1
        else:
            user_pair = pair2
        
        for m in g["Moves"]:
            if int(m[1]) == g["usernames"].index(player_name) + 1:     # if it is a user name
                moves_made += 1
                if m[1] == "1":
                    c = cost(state, user_pair, m, data)
                    deviance += c - np.average(comp_data[user_pair][str(state)])
                else:
                    c = cost(flip_state(state), user_pair, m, data)
                    deviance += c - np.average(comp_data[user_pair][str(flip_state(state))])
            do_action(m,state)
    
    return deviance/moves_made, deviance

x = []
y = []

for p in db.players.find({"Played":{"$gt":20}}):
    if p["Username"] in ["cptKav","probablytom","apropos0"]:
        continue
    dev_move, dev = find_deviance(p["Username"])
    #print("{0} Played {1} games with a deviance of {2}/action and a total deviance of {3}".format(p["Username"], p["Played"], dev_move, dev))
    x += [dev_move]
    y += [p["Won"]/p["Played"]]

x = np.array(x, dtype=float)
y = np.array(y, dtype=float)

plt.scatter(x,y)
plt.axhline(y=0.5)
plt.axvline(x=0.0)

# best fit
denom = x.dot(x) - x.mean() * x.sum()
m = ( x.dot(y) - y.mean() * x.sum() ) / denom
b = ( y.mean() * x.dot(x) - x.mean() * x.dot(y) ) / denom
y_pred = m*x+b

plt.plot(x, y_pred, "r")

plt.gca().invert_xaxis()
plt.title("Cost as a ranking")
plt.xlabel("Cost deviance per move")
plt.ylabel("Win ratio (%)")

print(m, b)

plt.tight_layout()
plt.show()