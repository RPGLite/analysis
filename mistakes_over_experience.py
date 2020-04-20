# William Kavanagh, April 2020

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math
from bson import objectid

cost_epsilon = 0.1     # TUNABLE: proportional change under which a cost can be disregarded
error_delta = 0.4       # TUNABLE: proportional change over which a cost can be considered 'major'

data = process_lookup2()       # Takes ~10 seconds

def flip_state(s):
    return [1] + s[10:] + s[1:10]


def get_mistakes_per_game(user, game):
    if game["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1"):
        return 0,0,0
    moves = 0
    mistakes = 0
    major_mistakes = 0
    state = get_initial_state(game)
    user_pair = game["p1c1"][0] + game["p1c2"][0]
    if game["usernames"].index(user) == 1:
        user_pair = game["p2c1"][0] + game["p2c2"][0]
    if chars.index(user_pair[0]) > chars.index(user_pair[1]):
        user_pair = user_pair[1] + user_pair[0]
    for m in game["Moves"]:
        if int(m[1]) - 1 == game["usernames"].index(user):
            if m[1] == "1":
                actual, possible = cost(state, user_pair, m, data, classify_mistake = True)
            else:
                #print(game, flip_state(state), user_pair, m)
                actual, possible = cost(flip_state(state), user_pair, m, data, classify_mistake = True)
            if possible > 0:
                moves += 1
                if (possible - actual) / possible > error_delta and possible > 0.1: # and game is winnable.
                    major_mistakes += 1
                    print("MAJOR MISTAKE: {0} chosen from {1} with a cost of {2} from {3}".format(m, state, possible-actual, possible))
                elif (possible - actual) / possible > cost_epsilon:
                    mistakes += 1
        do_action(m, state)
    return moves, mistakes, major_mistakes

results = {}


for u in db.players.find({"Username": {"$exists": True}, "elo": {"$exists": True}, "Played": {"$gt": 0}}):
    games = []
    for g in db.completed_games.find({"usernames": u["Username"], "winner": {"$exists": True}}):
        # for every game
        games += [g]
    games = sorted(games, key=lambda i: i['end_time'])
    for i in range(len(games)):
        if i not in results.keys():
            results[i] = [0,0,0]
        moves, mistakes, majors = get_mistakes_per_game(u["Username"], games[i])    
        results[i][0] += moves
        results[i][1] += mistakes
        results[i][2] += majors
       
#print(results)


cut_off = False
for i in range(max(results.keys())+1):
    if cut_off:
        results.pop(i)
    elif results[i][0] < 40:
        results.pop(i)
        cut_off = True

b1 = plt.bar(range(max(results.keys())+1),
        [results[i][2]/results[i][0] for i in range(max(results.keys())+1)],
        label = "Major errors: cost/optimal > {0}".format(error_delta))
b2 = plt.bar(range(max(results.keys())+1),
        [results[i][1]/results[i][0] for i in range(max(results.keys())+1)],
        bottom=[results[i][2]/results[i][0] for i in range(max(results.keys())+1)],
        label="Minor errors: cost/optimal > {0}".format(cost_epsilon))
plt.legend(loc=1)

# plt.bar(range(max(results.keys())),
#         [results[i].count(0.0) for i in range(max(results.keys()))])
# plt.bar(range(max(results.keys())),
#         [len(results[i]) - results[i].count(0.0)
#          for i in range(max(results.keys()))],
#         bottom=[results[i].count(0.0) for i in range(max(results.keys()))])

ax2 = plt.twinx()
plt.plot(range(max(results.keys())+1),
         [results[i][0] for i in range(max(results.keys())+1)])


plt.show()
