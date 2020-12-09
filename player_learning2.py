# William
# Generate line graphs for comparison of the average cost of moves comparing player experience and days since release.

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math, pymongo
from bson import objectid


# Some tunable constants
minimum_played = 3
bucket_count = 15

s1 = process_lookup("beta")
s2 = process_lookup("tango-2-3")

set_config("beta")

def legal_move(state, move):

    # Can always skip.
    if "skip" in move:
        return True

    if len(move) < 3:
        return False    # ?

    # If actor can't act.
    if state[chars.index(move[0])+1] == 0 or state[9] == chars.index(move[0]):
        return False

    # target isn't targetable
    if state[chars.index(move[2])+10] == 0:
        return False

    # Archer second target not targetable
    if move[0] == "A" and len(move) > 3:
        if state[chars.index(move[3])+10] == 0:
            return False

    # Healer heal target
    if move[0] == "H" and len(move) > 3:
        if state[chars.index(move[3])+1] == 0 or state[chars.index(move[3])+1] == set_health(full_name(move[3])):
            return False

    return True

def get_cost(log, s):
    state = [1]
    for i in range(len(chars)):
        if chars[i] == log["uc1"]:
            state += [int(log["uc1_health"])]
        elif chars[i] == log["uc2"]:
            state += [int(log["uc2_health"])]
        else:
            state += [0]
    if log["uc1_stun"] == "True":
        state += [chars.index(log["uc1"]) + 1]
    elif log["uc2_stun"] == "True":
        state += [chars.index(log["uc2"]) + 1]
    else:
        state += [0]
    # p2 states
    for i in range(len(chars)):
        if chars[i] == log["oc1"]:
            state += [int(log["oc1_health"])]
        elif chars[i] == log["oc2"]:
            state += [int(log["oc2_health"])]
        else:
            state += [0]
    if log["oc1_stun"] == "True":
        state += [chars.index(log["oc1"]) + 1]
    elif log["oc2_stun"] == "True":
        state += [chars.index(log["oc2"]) + 1]
    else:
        state += [0]

    # State 

    move = ""
    for c in log["action"]:
        if c in chars:
            move += c
            if "_" not in move:
                move += "_"

    pair = log["uc1"]+log["uc2"]
    if chars.index(pair[0]) > chars.index(pair[1]):
        pair = pair[1] + pair[0]

    if legal_move(state,move):
        if check_actions_available(state, pair, 0.15, s):
            v, max_p = cost(state, pair, move, s, classify_mistake=True)
            return (max_p - v) / max_p
            
    return 0

fig, (ax0, ax1) = plt.subplots(ncols=2, nrows=1, figsize=(10,4))

"""
for p in db.players.find({"Username":{"$exists":True}}):
    if p["Username"] in ["probablytom", "cptKav", "Ellen"]:          # Do not process the devs, they should know better. Also Frp97 has several impossible moves logged.
        continue
   
   
    


    # If player played enough S1 games, then process those games.
    if db.page_hits.count_documents({"user_move":"True", "user":p["Username"], "balance_code":{"$exists":False}, "kind":"move_viewed", "error":{"$exists":False}}) > 1000:# and db.completed_games.count_documents({"winner":{"$exists":True}, "balance_code":{"$exists":True}, "usernames":p["Username"]}) > 50 :
        costs = []
        results = []

        for m in db.page_hits.find({"user_move":"True", "user":p["Username"], "balance_code":{"$exists":False}, "kind":"move_viewed", "error":{"$exists":False}}):
            costs += [get_cost(m, s1)]

        start = np.mean(costs[:100])
        end = np.mean(costs[-100:])

        #print(p["Username"], start, end, len(costs), "season 1")

        # x = [x/len(costs) for x in range(len(costs))]

        # coefs = np.polyfit(x,costs,1)
        # poly = np.poly1d(coefs)

        # new_x = np.linspace(x[0],x[-1])
        # new_y = poly(new_x)

        # clump_costs = [np.mean(costs[y*5:y*5+4]) for y in range(len(costs)/5)]

        #ax0.scatter(range(len(costs)),costs)
        # results[p["Username"]] = {"delta":poly(1) - poly(0),"actions":len(costs)}
        # ax0.plot(new_x, new_y, label = p["Username"] + " - " + str(len(costs)))
        #print(len(costs), costs.count(0))

        # process costs[] and sort them into 20 buckets under results[]
        for i in range(bucket_count):
            bucket_values = []
            for j in range(math.floor(len(costs)/bucket_count)):
                bucket_values += [costs[j+(i*math.floor(len(costs)/bucket_count))]]
            #print(p["Username"], len(bucket_values), sum(bucket_values))
            results += [sum(bucket_values)/len(bucket_values)]
        x = [x/len(results) for x in range(len(results))]
        coefs = np.polyfit(x,results,1)
        poly = np.poly1d(coefs)

        new_x = np.linspace(x[0],x[-1])
        new_y = poly(new_x)
        #ax0.scatter(x, results)
        ax0.plot(new_x, new_y)
        if new_y[0] > new_y[1]:
            print(p["Username"], "got better")
        else:
            print(p["Username"], "got worse")


#ax0.scatter(range(len(results)), results)
#x = [x/len(results) for x in range(len(results))]


# for p in results:
#     print("{0}'s expected cost changed by {1}".format(p, results[p]))
# ax0.legend()
# results = dict(sorted(results.items(), key = lambda x: x[1]["actions"]))

# x = np.arange(len(results))
# ax0.bar(x, [results[p]["delta"] for p in results])
# ax0.set_xticks(x)
# ax0.set_xticklabels([results[p]["actions"] for p in results], rotation=90)
ax0.title.set_text("Season 1")
ax0.set_ylim([0, 0.05])
ax0.set_xlabel("Proportion of critical moves made")
ax0.set_ylabel("Average relative cost of moves in bucket")


"""
set_config("tango-2-3")


better = 0
worse = 0

print("SEASON 2")

for p in db.players.find({"Username":{"$exists":True}}):
    if p["Username"] in ["probablytom", "cptKav", "Ellen"]:          # Do not process the devs, they should know better.
        continue

    if p["Username"] not in ["Anakhand"]:
        continue


    # If player played enough S1 games, then process those games.
    if db.page_hits.count_documents({"user_move":"True", "user":p["Username"], "balance_code":{"$exists":True}, "kind":"move_viewed", "error":{"$exists":False}}) > 10:# and db.completed_games.count_documents({"winner":{"$exists":True}, "balance_code":{"$exists":True}, "usernames":p["Username"]}) > 50 :
        costs = []
        results = []

        for m in db.page_hits.find({"user_move":"True", "user":p["Username"], "balance_code":{"$exists":True}, "kind":"move_viewed", "error":{"$exists":False}}):
            costs += [get_cost(m, s2)]
        
            

        start = sum(i > 0.2 for i in costs[:200])
        #mid = np.mean(costs[math.floor(len(costs)/2)-51:math.floor(len(costs)/2) + 50])
        end = sum(i > 0.2 for i in costs[-200:])

       

        # if len(costs) > 400:
        #     plt.plot(["start","end"], [start,end], label = p["Username"])
        #     if end > start:
        #         print("{0} got worse".format(p["Username"]))
        #         worse += 1
        #     else:
        #         print("{0} got better".format(p["Username"]))
        #         better += 1

        #print(p["Username"], start, mid, end, len(costs), "season 2")
            
            # if len(costs) > 100:
            #     break

#         x = [x/len(costs) for x in range(len(costs))]

#         coefs = np.polyfit(x,costs,1)
#         poly = np.poly1d(coefs)

#         new_x = np.linspace(x[0],x[-1])
#         new_y = poly(new_x)
        ax1.scatter(range(len(costs)),costs)
        # print(len(costs), costs.count(0))

#         results[p["Username"]] = {"delta":poly(1) - poly(0),"actions":len(costs)}
#         ax1.plot(new_x, new_y, label = p["Username"] + " - " + str(len(costs)))
        for i in range(bucket_count):
            bucket_values = []
            for j in range(math.floor(len(costs)/bucket_count)):
                bucket_values += [costs[j+(i*math.floor(len(costs)/bucket_count))]]
            results += [sum(bucket_values)/len(bucket_values)]

        #ax1.scatter(range(len(results)), results)
        #x = [x/len(results) for x in range(len(results))]

        x = [x/len(results) for x in range(len(results))]
        coefs = np.polyfit(x,results,1)
        poly = np.poly1d(coefs)

        new_x = np.linspace(x[0],x[-1])
        new_y = poly(new_x)
        #ax1.scatter(x, results)
        ax1.plot(new_x, new_y)
        if new_y[0] > new_y[1]:
            print(p["Username"], "got better")
        else:
            print(p["Username"], "got worse")


# print("worse {0}".format(worse))
# print("better {0}".format(better))
# plt.legend()

# ax1.title.set_text("Season 2")
# ax1.set_ylim([0, 0.05])
# ax1.set_xlabel("Proportion of critical moves made")
# ax1.set_ylabel("Average relative cost of moves in bucket")
plt.tight_layout()

plt.savefig(r"C:\Users\bkav9\OneDrive\Pictures\figures\top_15_1d_learning.png")

plt.show()



# for p in results:
#     print("{0}'s expected cost changed by {1}".format(p, results[p]))


# results = dict(sorted(results.items(), key = lambda x: x[1]["actions"]))


# x = np.arange(len(results))
# ax1.bar(x, [results[p]["delta"] for p in results])
# ax1.set_xticks(x)
# ax1.set_xticklabels([results[p]["actions"] for p in results], rotation = 90)
# ax1.set_xlabel("Users (and number of moves made, ascending order)")
# ax1.set_ylabel("")
# ax1.set_ylabel("Change in expected cost per move between first and last move")

# plt.tight_layout()    
# plt.show()

        
# # Show number of games played. Order and colour the results?\


# TODO: Find users where there is fittable data.