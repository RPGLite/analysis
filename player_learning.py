# William
# Generate line graphs for comparison of the average cost of moves comparing player experience and days since release.

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math, pymongo
from bson import objectid
import seaborn as sns

# Some tunable constants
minimum_played = 3
bucket_interval = 10
critical_section_delta = 0.1            # value above 0.0 and below 1.0 at which the game is still in progress.


def flip_state(s):
    return [1] + s[10:] + s[1:10]

s1 = process_lookup("beta")
#s2 = process_lookup("tango-2-3")

def get_cost_list(g, p, lookup):
    """
    Return a list of costs per move of all critical moves made by the player
    """
    costs = []  # return list
    # Ignore dodgy games
    if g["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1") or g["_id"] == objectid.ObjectId("5eaaee2c684de5692fc01ef6") or g["_id"] == objectid.ObjectId("5ec108ef29108c1ba22cb375"):    
        return costs    # just leave.

    state = get_initial_state(g)                # store game state, initialised to game start.
    pos = g["usernames"].index(p) + 1           # pos 1 = p is player 1.
    pair = g["p1c1"][0] + g["p1c2"][0] if pos==1 else g["p2c1"][0] + g["p2c2"][0]
    if chars.index(pair[0]) > chars.index(pair[1]):
        pair = pair[1]+pair[0]      # correct ordering

    for m in g["Moves"]:
        if m[1] == str(pos):        # if it is the player's turn
            if pos == 1:
                act, max_poss = cost(state, pair, m, lookup, classify_mistake=True)    # actual P() and maximum possible P()
                if check_actions_available(state, pair, critical_section_delta, lookup):
                    costs += [(max_poss - act) / max_poss]
                # print(state, pair, max_poss, count_actions_available(state, pair, lookup))

            else:
                act, max_poss = cost(flip_state(state), pair, m, lookup, classify_mistake=True)    # actual P() and maximum possible P()
                if check_actions_available(flip_state(state), pair, critical_section_delta, lookup):
                    costs += [(max_poss - act) / max_poss]
                # print(state, pair, max_poss, count_actions_available(flip_state(state), pair, lookup))
        do_action(m, state)

    return costs

s1results = {}
s2results = {}

set_config("beta")

all_buckets = []

for p in db.players.find({"Username":{"$exists":True}}):
    if p["Username"] in ["probablytom", "cptKav", "Ellen"]:          # Do not process the devs, they should know better.
        continue

    player_costs = []
    # If player played enough S1 games, then process those games.
    if db.completed_games.count_documents({"winner":{"$exists":True}, "balance_code":{"$exists":False}, "usernames":p["Username"]}) >= 50:
        for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":{"$exists":False}, "usernames":p["Username"]}).sort("end_time", pymongo.ASCENDING)[:50]:
            player_costs += get_cost_list(g, p["Username"], s1)

        x = []
        y = []

        print(len(player_costs))

        for j in range(math.floor(len(player_costs)/bucket_interval)):
            x += [j]
            vals = []
            for k in range(bucket_interval):
                vals += [player_costs[j*bucket_interval + k]]
            y += [np.average(vals)]        

        print(len(y))

        for i in range(len(y)):
            if i >= len(all_buckets) or len(all_buckets) == 0:
                all_buckets += [y]
            else:
                all_buckets[i] += y

        coefs = np.polyfit(x,y,2)
        poly = np.poly1d(coefs)

        new_x = np.linspace(x[0],x[-1])
        new_y = poly(new_x)

        plt.plot(new_x, new_y, label = p["Username"], alpha = 0.3)
               
        # plt.scatter(x,y, label=p["Username"])
        # plt.plot(np.poly1d(player_costs), label="trend")

        # plt.plot(
        #     [np.mean(player_costs[x*15:(x*15)+14]) for x in range(math.floor(len(player_costs)/15) - 1)], 
        #     label=p["Username"]
        # )




x = range(len(all_buckets))[:50]
y = [np.mean(all_buckets[i]) for i in x]
coefs = np.polyfit(x,y,2)
poly = np.poly1d(coefs)
#print(y)
plt.scatter(x,y)

new_x = np.linspace(x[0],x[-1])
new_y = poly(new_x)

plt.plot(new_x, new_y, label = "overal")
plt.xlim([x[0]-1, x[-1] + 1 ])
plt.ylim(0,0.25)

plt.legend()
plt.show() 
"""

# for each player:
for p in db.players.find({"Username":{"$exists":True}}):
    if p["Username"] in ["probablytom", "cptKav", "Ellen"]:          # Do not process the devs, they should know better.
        continue

    # If player played enough S1 games, then process those games.
    if db.completed_games.count_documents({"winner":{"$exists":True}, "balance_code":{"$exists":False}, "usernames":p["Username"]}) >= minimum_played:
        # for every season 1 they played in
        set_config("beta")      # set constants to season 1
        games_in_current_bucket = 0
        bucket_count = 0
        current_bucket = []
        for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":{"$exists":False}, "usernames":p["Username"]}).sort("end_time", pymongo.ASCENDING):
            costs = get_cost_list(g, p["Username"], s1)
            if games_in_current_bucket < bucket_interval:
                current_bucket += costs
                games_in_current_bucket += 1
            else:
                if bucket_count not in s1results:
                    s1results[bucket_count] = {"costs":[], "mistakes10":0, "mistakes20":0, "mistakes30":0, "mistakes40":0, "mistakes50":0, "count":0}
                s1results[bucket_count]["costs"] += current_bucket
                s1results[bucket_count]["mistakes10"] += sum(i > 0.1 for i in current_bucket)
                s1results[bucket_count]["mistakes20"] += sum(i > 0.2 for i in current_bucket)
                s1results[bucket_count]["mistakes30"] += sum(i > 0.3 for i in current_bucket)
                s1results[bucket_count]["mistakes40"] += sum(i > 0.4 for i in current_bucket)
                s1results[bucket_count]["mistakes50"] += sum(i > 0.5 for i in current_bucket)
                s1results[bucket_count]["count"] += bucket_interval
                bucket_count += 1
                current_bucket = []
                games_in_current_bucket = 0

    # If player didn't play enough S2 games, go to next player
    if db.completed_games.count_documents({"winner":{"$exists":True}, "balance_code":{"$exists":True}, "usernames":p["Username"]}) < minimum_played:
        continue
    set_config("tango-2-3")     # set constants to season 2
    games_in_current_bucket = 0
    bucket_count = 0
    current_bucket = []
    for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":{"$exists":True}, "usernames":p["Username"]}).sort("end_time", pymongo.ASCENDING):
        costs = get_cost_list(g, p["Username"], s2)
        if games_in_current_bucket < bucket_interval:
            current_bucket += costs
            games_in_current_bucket += 1
        else:
            if bucket_count not in s2results:
                s2results[bucket_count] = {"costs":[], "mistakes10":0, "mistakes20":0, "mistakes30":0, "mistakes40":0, "mistakes50":0, "count":0}
            s2results[bucket_count]["costs"] += current_bucket
            s2results[bucket_count]["mistakes10"] += sum(i > 0.1 for i in current_bucket)
            s2results[bucket_count]["mistakes20"] += sum(i > 0.2 for i in current_bucket)
            s2results[bucket_count]["mistakes30"] += sum(i > 0.3 for i in current_bucket)
            s2results[bucket_count]["mistakes40"] += sum(i > 0.4 for i in current_bucket)
            s2results[bucket_count]["mistakes50"] += sum(i > 0.5 for i in current_bucket)
            s2results[bucket_count]["count"] += bucket_interval
            bucket_count += 1
            current_bucket = []
            games_in_current_bucket = 0



fig, (ax0, ax1) = plt.subplots(nrows=2, ncols=1)

max_bucket = 0
for i in s1results.keys():
    if s1results[i]["count"] >= 21:
        max_bucket = i
    else:
        break

labels = list(s1results[0].keys())
for series in labels[1:-1]:
    ax0.plot(["<{0}".format((x*bucket_interval)+bucket_interval-1) for x in range(max_bucket)],
    [s1results[i][series]/(s1results[i]["count"]) for i in range(max_bucket)], 
    label = series)
ax0.set_title("SEASON 1")

# Grey out the above, Add rate of learning (best fit for groups of buckets)

# Reciprical regression link: https://blog.minitab.com/blog/adventures-in-statistics-2/curve-fitting-with-linear-and-nonlinear-regression

ax0.legend()

f2 = plt.figure(1)
max_bucket = 0
for i in s2results.keys():
    if s2results[i]["count"] >= 21:
        max_bucket = i
    else:
        break

labels = list(s2results[0].keys())
for series in labels[1:-1]:
    ax1.plot(["<{0}".format((x*bucket_interval)+bucket_interval-1) for x in range(max_bucket)],
    [s2results[i][series]/(s2results[i]["count"]) for i in range(max_bucket)], 
    label = series)

ax1.set_title("SEASON 2")

ax1.legend()
plt.tight_layout()
plt.show()

"""