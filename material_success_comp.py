import pymongo
from bson import objectid
from helper_fns import *
import matplotlib.pyplot as plt
import numpy as np

results = {}

for p in pairs:
    results[p] = {q:0 for q in pairs}

for g in db.completed_games.find({"balance_code":{"$exists":False}, "winner":{"$exists":True}}):
    p1 = g["p1c1"][0]+g["p1c2"][0]
    p2 = g["p2c1"][0]+g["p2c2"][0]
    if chars.index(p1[0]) > chars.index(p1[1]):
        p1 = p1[1] + p1[0]
    if chars.index(p2[0]) > chars.index(p2[1]):
        p2 = p2[1] + p2[0]
    if g["winner"] == 1:
        results[p1][p2] += 1
    else:
        results[p2][p1] += 1

# Generate CSV
# row1 = ","
# for p in results:
#     row1 += p + ","
# #    print(p, results[p])

# print(row1)
# for p in results:
#     row = p + ","
#     for q in pairs:
#         row += str(results[p][q]) + ","
#     print(row)

c=0
for p in pairs:
    for q in pairs:
        if results[p][q] + results[q][p] == 0:
            if p == q:
                c += 1
            else:
                c += 0.5
            print(p,q)
    # won = sum(results[p].values())
    # lost = sum([results[q][p] for q in pairs])
    # win_ratio = won / (won+lost)
    # best_matchup = p
    # best_matchup_won = 0
    # best_matchup_lost = 1
    # for q in pairs:
    #     if results[p][q] + results[q][p] < 5:
    #         continue
        
    #     if results[p][q]/(results[p][q]+results[q][p]) > best_matchup_won / (best_matchup_lost + best_matchup_won):
    #         best_matchup = q
    #         best_matchup_wn = results[p][q]
    #         best_matchup_lost = results[q][p] 
    # worst_matchup = p

    # print("{0} played {1} games with a win-ratio of {2:.3f},\ttheir best matchup was {3} with a record of {4}:{5}, their worst was {6} with a matchup of {7}:{8}".format(
    #     p, won+lost, win_ratio, best_matchup, best_matchup_won, best_matchup_lost, worst_matchup, 0, 0
    # ))
print(c)