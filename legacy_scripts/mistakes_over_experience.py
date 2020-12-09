# William Kavanagh, April 2020

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math
from bson import objectid
import copy

cost_epsilon = 0.05     # TUNABLE: proportional change under which a cost can be disregarded
error_delta = 0.25       # TUNABLE: proportional change over which a cost can be considered 'major'

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
                    #print("MAJOR MISTAKE: {0} chosen from {1} with a cost of {2} from {3}".format(m, state, possible-actual, possible))
                elif (possible - actual) / possible > cost_epsilon:
                    mistakes += 1
        do_action(m, state)
    return moves, mistakes, major_mistakes

results = {}
num_games = []

for u in db.players.find({"Username": {"$exists": True}, "elo": {"$exists": True}, "Played": {"$gt": 0}}):
    games = []
    num_games += [db.completed_games.count_documents(
        {"usernames": u["Username"], "winner": {"$exists": True}})]
    for g in db.completed_games.find({"usernames": u["Username"], "winner": {"$exists": True}, "balance_code": {"$exists": False}}):
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
       

cumulative_results = copy.deepcopy(results)

cut_off = 0
for i in range(max(results.keys())+1):
    if i > 0:
        for j in range(3):
            cumulative_results[i][j] += cumulative_results[i-1][j]
    if results[i][0] < 40 and cut_off == 0:
        cut_off = i
    
print(results)

    
for i in range(max(results.keys())+1):
    if i > cut_off:
        results.pop(i)

print(results)

print("\n\n", cumulative_results)

fig, (ax1, ax2, ax3) = plt.subplots(nrows = 3, ncols = 1)

# ax1.bar(range(max(results.keys())+1),
#         [results[i][2]/results[i][0] for i in range(max(results.keys())+1)],
#         label = "Major errors: cost/optimal > {0}".format(error_delta))
# ax1.bar(range(max(results.keys())+1),
#         [results[i][1]/results[i][0] for i in range(max(results.keys())+1)],
#         bottom=[results[i][2]/results[i][0] for i in range(max(results.keys())+1)],
#         label="Minor errors: cost/optimal > {0}".format(cost_epsilon))
# ax1.legend(loc=1)
num_game_steps = []
for j in range(0,max(num_games),5):
    num_game_steps += [sum(i >= j for i in num_games) ] 
ax1.plot(range(0, max(num_games), 5), num_game_steps)

# plt.bar(range(max(results.keys())),
#         [results[i].count(0.0) for i in range(max(results.keys()))])
# plt.bar(range(max(results.keys())),
#         [len(results[i]) - results[i].count(0.0)
#          for i in range(max(results.keys()))],
#         bottom=[results[i].count(0.0) for i in range(max(results.keys()))])

# ax1_2 = ax1.twinx()
# ax1_2.plot(range(1,max(results.keys())+1),
#          [results[i][0]-results[i-1][0] for i in range(1,max(results.keys())+1)])

ax2.bar(range(max(cumulative_results.keys())+1),
        [cumulative_results[i][2]/cumulative_results[i][0]
                 for i in range(max(cumulative_results.keys())+1)],
             label="Major errors: cost/optimal > {0}".format(error_delta))
ax2.legend(loc=1)

ax3.bar(range(max(cumulative_results.keys())+1),
        [(cumulative_results[i][1]+cumulative_results[1][2])/cumulative_results[i][0]
         for i in range(max(cumulative_results.keys())+1)],
        
        label="Minor errors: cost/optimal > {0}".format(cost_epsilon))
ax3.legend(loc=1)

# plt.bar(range(max(cumulative_results.keys())),
#         [cumulative_results[i].count(0.0) for i in range(max(cumulative_results.keys()))])
# plt.bar(range(max(cumulative_results.keys())),
#         [len(cumulative_results[i]) - cumulative_results[i].count(0.0)
#          for i in range(max(cumulative_results.keys()))],
#         bottom=[cumulative_results[i].count(0.0) for i in range(max(cumulative_results.keys()))])

# ax2_2 = ax2.twinx()
# ax2_2.plot(range(1,max(cumulative_results.keys())+1),
#          [cumulative_results[i][0]-cumulative_results[i-1][0] for i in range(1,max(cumulative_results.keys())+1)])


#ax3.plot(num_games, range(len(num_games)))


# ax4.bar(range(1,51),
#         [(cumulative_results[i][1]+cumulative_results[i][2])/cumulative_results[i][0] - (cumulative_results[i-1][1]+cumulative_results[i-1][2])/cumulative_results[i-1][0]
#          for i in range(1, 51)],
#         label="Minor errors: cost/optimal > {0}".format(cost_epsilon))
# ax4.axhline(y=0.0)


# ax5.bar(range(51,max(cumulative_results.keys())+1),
#         [(cumulative_results[i][1]+cumulative_results[i][2])/cumulative_results[i][0] - (cumulative_results[i-1][1]+cumulative_results[i-1][2])/cumulative_results[i-1][0]
#          for i in range(51,max(cumulative_results.keys())+1)],
        
#              label="Minor errors: cost/optimal > {0}".format(cost_epsilon))
# ax5.set_ylim([-0.02,0.02])
# ax5.axhline(y=0.0)



plt.tight_layout()
plt.show()
