# William Kavanagh, June 2020

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math
from bson import objectid

s1data = process_lookup("beta")
#s2data = process_lookup("tango-2-3")       

def flip_state(s):
    return [1] + s[10:] + s[1:10]

s1 = {}
s2 = {}

# Process S1 games
set_config("beta")
for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":{"$exists":False}}):#"1.2"}):
    if g["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1"):    # Ignore dodgy game.
        continue
    if g["_id"] == objectid.ObjectId("5eaaee2c684de5692fc01ef6") or g["_id"] == objectid.ObjectId("5ec108ef29108c1ba22cb375"):    # Ignore dodgy game.
        continue
    state = get_initial_state(g)
    pair1 = g["p1c1"][0] + g["p1c2"][0]
    pair2 = g["p2c1"][0] + g["p2c2"][0]
    if chars.index(pair1[0]) > chars.index(pair1[1]):
        pair1 = pair1[1]+pair1[0]
    if chars.index(pair2[0]) > chars.index(pair2[1]):
        pair2 = pair2[1]+pair2[0]
    for m in g["Moves"]:
        if m[1] == "1":                        
            c = cost(state, pair1, m, s1data)
            if str(state) in s1:
                s1[str(state)] += [c]
            else: 
                s1[str(state)] = [c]
        elif m[1] == "2":
            c = cost(flip_state(state), pair2, m, s1data)
            if str(flip_state(state)) in s1:
                s1[str(flip_state(state))] += [c]
            else: 
                s1[str(flip_state(state))] = [c]

        do_action(m, state)

for s in s1.keys():
    c = np.average(s1[s])
    l = len(s1[s])
    m = sum(v > 0 for v in s1[s])
    s1[s] = {"cost": c, "visits":l, "mistakes":m/l}

def find_worst_n_moves_seen_m_times(n,m):
    ret_list = []
    ret_list_values = []
    for item in range(n):
        ret_list_values += [0]
        ret_list += [""]
    for s in s1.keys():
        if s1[s]["visits"] >= m:
            for i in range(n):
                if s1[s]["cost"] > ret_list_values[i]:
                    tmp_v = ret_list_values[i]
                    tmp = ret_list[i]
                    ret_list_values[i] = s1[s]["cost"]
                    ret_list[i] = s
                    for j in range(i,n):
                        if tmp_v > ret_list_values[j]:
                            other_tmp_v = ret_list_values[j]
                            other_tmp = ret_list[j]
                            ret_list_values[j] = tmp_v
                            ret_list[j] = tmp
                            tmp_v = other_tmp_v
                            tmp = other_tmp
                    break
    #return ret_list, ret_list_values
    for r in ret_list:
        print(r, s1[r])

def find_worse_with_over_n_moves(n):
    current = ""
    max = 0.0
    for state in s1.keys():
        if s1[state]["cost"] > max and s1[state]["visits"] > n:
            max = val
            current = state
    print("Worst state with at least " + str(n) + " moves is: " + current)
    print("move was made " + str(len(s1[current])) + " times with an average cost of: " + str(max))

def find_move_mistakes_with_over_n_moves(n):
    current = ""
    max = 0.0
    for state in s1.keys():
        if s1[state]["mistakes"] > max and s1[state]["visits"] > n:
            max = s1[state]["mistakes"]
            current = state
    print("Worst state with at least " + str(n) + " moves is: " + current)
    print("{0} mistakes were made out of {1} visists".format(s1[current]["mistakes"]*s1[current]["visits"], s1[current]["visits"]))

# find_worse_with_over_n_moves(1)
# find_worse_with_over_n_moves(5)
# find_worse_with_over_n_moves(10)
# find_worse_with_over_n_moves(20)
# find_worse_with_over_n_moves(40)
# find_worse_with_over_n_moves(80)
# find_worse_with_over_n_moves(100)

#find_worst_n_moves_seen_m_times(30,9)

# s = "[1, 0, 0, 0, 8, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 0, 0]"
# print(s1[s])

s1.pop("[1, 0, 0, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0]")
s1.pop("[1, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 10, 0, 0]")

find_move_mistakes_with_over_n_moves(5)
find_move_mistakes_with_over_n_moves(15)
find_move_mistakes_with_over_n_moves(25)
find_move_mistakes_with_over_n_moves(35)
find_move_mistakes_with_over_n_moves(45)