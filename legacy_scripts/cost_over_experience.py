# William Kavanagh, April 2020

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math
from bson import objectid

data = process_lookup2()       # Takes ~10 seconds

def flip_state(s):
    return [1] + s[10:] + s[1:10]


def get_cost_per_game(user, game):
    if game["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1"):
        return 0.0
    costs = []
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
                #print(game, flip_state(state), user_pair, m)
                costs += [cost(flip_state(state), user_pair, m, data)]
        if game["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1"):
            print(m, state)

        do_action(m, state)
    if math.isnan(np.average(costs)):
        # The player didn't get a single turn (monk flurry killed them turn 1, poor guy)
        return 0.0
    return np.average(costs)

results = {}

for u in db.players.find({"Username": {"$exists": True}, "elo": {"$exists": True}, "Played": {"$gt": 0}}):
    games = []
    for g in db.completed_games.find({"usernames": u["Username"], "winner": {"$exists": True}}):
        # for every game
        games += [g]
    games = sorted(games, key=lambda i: i['end_time'])
    for i in range(len(games)):
        if i in results.keys():
            results[i] += [get_cost_per_game(u["Username"], games[i])]
        else:
            results[i] = [get_cost_per_game(u["Username"], games[i])]
            
# results = {0: [0.01, 0.0, 0.023,x], <num_games_played>: [<list_of_costs>], .. }
        
        
    
for i in range(max(results.keys())+1):
    print(i, np.average(results[i]), len(results[i]), results[i].count(0.0)/len(results[i]))
    if len(results[i]) < 20:
        results.pop(i)
        
print(results)

plt.bar(range(max(results.keys())),
        [results[i].count(0.0) for i in range(max(results.keys()))])
plt.bar(range(max(results.keys())),
        [len(results[i]) - results[i].count(0.0)
         for i in range(max(results.keys()))],
        bottom=[results[i].count(0.0) for i in range(max(results.keys()))])

ax2 = plt.twinx()
plt.plot(range(max(results.keys())),
         [results[i].count(0.0)/len(results[i]) for i in range(max(results.keys()))])


plt.show()
