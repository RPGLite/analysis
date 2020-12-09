# William Kavanagh, April 2020

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math
from bson import objectid

data = process_lookup2()       

def flip_state(s):
    return [1] + s[10:] + s[1:10]


def find_avg_cost_per_move(user):
    costs = []
    for game in find_games_with_user(user):
        if game["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1"):
            continue
        state = get_initial_state(game)
        user_pair = game["p1c1"][0] + game["p1c2"][0]
        if game["usernames"].index(user) == 1:
            user_pair = game["p2c1"][0] + game["p2c2"][0]
        if chars.index(user_pair[0]) > chars.index(user_pair[1]):
            user_pair = user_pair[1] + user_pair[0]
        for m in game["Moves"]:
            if int(m[1]) - 1 == game["usernames"].index(user):
                if m[1] == "1":                        
                    costs += [cost(state, user_pair, m, data)]
                   
                else:
                    costs += [cost(flip_state(state), user_pair, m, data)]
            do_action(m, state)
            if state[0] < 1 or state[0] > 1:
                exit
    return np.average(costs)


cost_l = []
elo_l = []
for u in db.players.find({"Username":{"$exists": True}, "elo":{"$exists": True}, "Played":{"$gt":0}}):
    # print("User:", u["Username"])
    # print("cost:", search_by_user(u["Username"]))
    # print("ELO:", u["elo"])
    c = find_avg_cost_per_move(u["Username"])
    if not math.isnan(c):
        cost_l += [c]
        elo_l += [u["elo"]]

print(np.average(cost_l))

fig, ax = plt.subplots(figsize=(16,8))
ax.scatter(elo_l, cost_l)
z = np.polyfit(elo_l, cost_l, 1)
p = np.poly1d(z)
plt.plot(np.unique(elo_l), np.poly1d(np.polyfit(elo_l, cost_l, 1))(np.unique(elo_l)))

plt.axvline(x=1200)
plt.axhline(y=np.average(cost_l))
plt.xlabel("ELO")
plt.ylabel("average cost per move")
plt.show()
