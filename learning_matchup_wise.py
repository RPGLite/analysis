# August '20 -- let's consider matchups users have seen before. do they get better there?

from helper_fns import *
from bson import objectid
import matplotlib.pyplot as plt
import numpy as np


s1 = process_lookup("beta")
s2 = process_lookup("tango-2-3")

def parse_player_in_season(p, season):

    matchups = {}
    pair_matchups = {}

    if what_config() != season:
            if season == 1:
                set_config("beta")
            else:
                set_config("tango-2-3")

    if season == 1:
        lookup = s1
        bc = {"$exists":False}
    else:
        lookup = s2
        bc = "1.2"

    for g in db.completed_games.find({"usernames":p,"winner":{"$exists":True}, "balance_code":bc}):
        if g["_id"] in [objectid.ObjectId("5e98b4658a225cfc82573fd1"), objectid.ObjectId("5eaaee2c684de5692fc01ef6"), objectid.ObjectId("5ec108ef29108c1ba22cb375")]:
            continue
        critical_moves = 0
        total_cost = 0.0
        if g["usernames"][0] == p:
            matchup = g["p1c1"][0]+g["p1c2"][0]+g["p2c1"][0]+g["p2c2"][0]
        else:
            matchup = g["p2c1"][0]+g["p2c2"][0]+g["p1c1"][0]+g["p1c2"][0]
        if chars.index(matchup[1]) < chars.index(matchup[0]):
            matchup = matchup[1]+matchup[0]+matchup[2]+matchup[3]
        if chars.index(matchup[3]) < chars.index(matchup[2]):
            matchup = matchup[0]+matchup[1]+matchup[3]+matchup[2]

        pair = matchup[:2]
        state = get_initial_state(g)

        for m in g["Moves"]: 
            # for every move
            if m[1] == str(g["usernames"].index(p)+1):
                # if the move was made by the player being processed.
                if m[1] == "1":
                    # if the player was player 1
                    if check_actions_available(state, pair, 0.05, lookup):

                        act,pos = cost(state,pair,m,lookup,classify_mistake=True)
                        critical_moves+=1
                        total_cost += (pos-act) / pos

                        #print("!")
                else:
                    if check_actions_available(flip_state(state), pair, 0.05, lookup):
                        act,pos = cost(flip_state(state),pair,m,lookup,classify_mistake=True)
                        critical_moves+=1
                        total_cost += (pos-act) / pos

                        #print("!")
            do_action(m, state)


        if critical_moves > 0:
            avg_cost = total_cost / critical_moves
            if avg_cost > 1:
                print("OK HOLD UP:", p)
                print(g)
            if matchup in matchups:
                matchups[matchup] += [avg_cost]
            else:
                matchups[matchup] = [avg_cost]

            if pair in pair_matchups:
                pair_matchups[pair] += [avg_cost]
            else:
                pair_matchups[pair] = [avg_cost]

    return matchups, pair_matchups

total_considered_matchups = 0
good_considered_matchups = 0
total_considered_pairs = 0
good_considered_pairs = 0


fig, (ax0, ax1) = plt.subplots(ncols=2, nrows=1, figsize=(15,3))
fig2, (ax0_, ax1_) = plt.subplots(ncols=2, nrows=1, figsize=(15,3))

s1_pair_results = []
s1_matchup_results = []
all_pairs_avg_calc = []
all_matchups_avg_calc = []

for q in db.players.find({"Username":{"$exists":True}}):

    # Remove devs
    if q["Username"] in ["probablytom", "cptKav"]:
        continue
    # Remove those who played fewer than 5 games
    if db.completed_games.count_documents({"winner":{"$exists":True}, "usernames":q["Username"], "balance_code":{"$exists":False}}) < 10:
        continue

    matchups,pair_matchups = parse_player_in_season(q["Username"],1)
    all_matchups = []
    all_pairs = []

    # For each matchup seen 3 or more times, find the learning rate and add it to a list.
    for m in matchups.keys():
        if len(matchups[m]) >= 3:    
            all_matchups += [np.polyfit(range(len(matchups[m])), matchups[m], 1)[0]]# * len(matchups[m])]
            all_matchups_avg_calc += [np.polyfit(range(len(matchups[m])), matchups[m], 1)[0]] * len(matchups[m])
            if np.polyfit(range(len(matchups[m])), matchups[m], 1)[0] < -0.3:
                print(q["Username"], "did extraordinarily")
                print(matchups)


    # If 5 or more matchups in total were seen 3 or more times, the player should be considered
    if len(all_matchups) >= 1:
        #print("Season 1: {0} played {1} games considered by matchups with an average change of: {2}".format(q["Username"], len(all_matchups), np.average(all_matchups)))
        if np.average(all_matchups) < 0:
            good_considered_matchups += 1
        total_considered_matchups += 1 
        s1_matchup_results += [np.average(all_matchups)]
  
    # For each pair used 5 for more times, find the rate of learning and add it to a list
    for p in pair_matchups:
        if len(pair_matchups[p]) >= 5:
            all_pairs += [np.polyfit(range(len(pair_matchups[p])), pair_matchups[p], 1)[0]]# * len(pair_matchups[p])]
            all_pairs_avg_calc += [np.polyfit(range(len(pair_matchups[p])), pair_matchups[p], 1)[0]] * len(pair_matchups[p])

    # If 5 or more pairs are seen 5 or more times, then consider that player
    #print(all_pairs)
    if len(all_pairs) >= 1:
        total_considered_pairs += 1
        if np.average(all_pairs) < 0:
            good_considered_pairs += 1
        #print("Season 1: {0} has {1} pairs played enough for consideration with an average change of: {2}".format(q["Username"], len(all_pairs), np.average(all_pairs)))
        s1_pair_results += [np.average(all_pairs)]

s1_matchup_results = sorted(s1_matchup_results)

for r in s1_matchup_results:
    ax0.bar(
        (s1_matchup_results.index(r)+1)/len(s1_matchup_results),
        r,
        0.5/len(s1_matchup_results),
        color="grey"
    )

ax0.axhline(y=0, linestyle='dotted')
#ax0.axhline(y=np.average(all_matchups_avg_calc))
print("Average season 1 matchup result: {0}".format(np.average(all_matchups_avg_calc)))

s1_pair_results = sorted(s1_pair_results)

for r in s1_pair_results:
    ax0_.bar(
        (s1_pair_results.index(r)+1)/len(s1_pair_results),
        r,
        0.5/len(s1_pair_results),
        color="grey"
    )

ax0_.axhline(y=0, linestyle='dotted')
#ax0_.axhline(y=np.average(all_pairs_avg_calc))
print("Average season 1 pair result: {0}".format(np.average(all_pairs_avg_calc)))

print("Of {0} players with matchups considered, {1} got better".format(total_considered_matchups, good_considered_matchups))
print("Of {0} players with pairs considered, {1} got better".format(total_considered_pairs, good_considered_pairs))

print("season 2")

total_considered_matchups = 0
good_considered_matchups = 0
total_considered_pairs = 0
good_considered_pairs = 0

s2_pair_results = []
s2_matchup_results = []
all_pairs_avg_calc = []
all_matchups_avg_calc = []

for q in db.players.find({"Username":{"$exists":True}}):

    # Remove devs
    if q["Username"] in ["probablytom", "cptKav"]:
        continue
    # Remove those who played fewer than 5 games
    if db.completed_games.count_documents({"winner":{"$exists":True}, "usernames":q["Username"], "balance_code":"1.2"}) < 10:
        continue

    matchups,pair_matchups = parse_player_in_season(q["Username"],2)
    all_matchups = []
    all_pairs = []

    # For each matchup seen 3 or more times, find the learning rate and add it to a list.
    for m in matchups.keys():
        if len(matchups[m]) >= 3:    
            all_matchups += [np.polyfit(range(len(matchups[m])), matchups[m], 1)[0]]# * len(matchups[m])]
            all_matchups_avg_calc += [np.polyfit(range(len(matchups[m])), matchups[m], 1)[0]] * len(matchups[m])

    # If 5 or more matchups in total were seen 3 or more times, the player should be considered
    if len(all_matchups) >= 1:
        #print("Season 2: {0} played {1} games considered by matchups with an average change of: {2}".format(q["Username"], len(all_matchups), np.average(all_matchups)))
        if np.average(all_matchups) < 0:
            good_considered_matchups += 1
        total_considered_matchups += 1 
        s2_matchup_results += [np.average(all_matchups)]
  
    # For each pair used 5 for more times, find the rate of learning and add it to a list
    for p in pair_matchups:
        if len(pair_matchups[p]) >= 5:
            all_pairs += [np.polyfit(range(len(pair_matchups[p])), pair_matchups[p], 1)[0]]# * len(pair_matchups[p])]
            all_pairs_avg_calc += [np.polyfit(range(len(pair_matchups[p])), pair_matchups[p], 1)[0]] * len(pair_matchups[p])
    
    # If 5 or more pairs are seen 5 or more times, then consider that player
    if len(all_pairs) >= 1:
        total_considered_pairs += 1
        if np.average(all_pairs) < 0:
            good_considered_pairs += 1
        #print("Season 2: {0} has {1} pairs played enough for consideration with an average change of: {2}".format(q["Username"], len(all_pairs), np.average(all_pairs)))
        s2_pair_results += [np.average(all_pairs)]


print("Of {0} players with matchups considered, {1} got better".format(total_considered_matchups, good_considered_matchups))
print("Of {0} players with pairs considered, {1} got better".format(total_considered_pairs, good_considered_pairs))

s2_matchup_results = sorted(s2_matchup_results)

for r in s2_matchup_results:
    ax1.bar(
        (s2_matchup_results.index(r)+1)/len(s2_matchup_results),
        r,
        0.5/len(s2_matchup_results),
        color="grey"
    )

ax1.axhline(y=0, linestyle='dotted')
#ax1.axhline(y=np.average(all_matchups_avg_calc))
print("Average season 2 matchup result: {0}".format(np.average(all_matchups_avg_calc)))


s2_pair_results = sorted(s2_pair_results)

for r in s2_pair_results:
    ax1_.bar(
        (s2_pair_results.index(r)+1)/len(s2_pair_results),
        r,
        0.5/len(s2_pair_results),
        color="grey"
    )

ax1_.axhline(y=0, linestyle='dotted')
#ax1_.axhline(y=np.average(all_pairs_avg_calc))
print("Average season 2 pair result: {0}".format(np.average(all_pairs_avg_calc)))


ax0.tick_params(
    axis='x',          # changes apply to the x-axis
    which='both',      # both major and minor ticks are affected
    bottom=False,      # ticks along the bottom edge are off
    top=False,         # ticks along the top edge are off
    labelbottom=False)
ax0.set_xlabel("Players")
ax0.set_ylabel("Average Change in Cost")
ax1.tick_params(
    axis='x',          # changes apply to the x-axis
    which='both',      # both major and minor ticks are affected
    bottom=False,      # ticks along the bottom edge are off
    top=False,         # ticks along the top edge are off
    labelbottom=False)
ax1.set_xlabel("Players")
ax1.set_ylabel("Average Change in Cost")
ax0_.tick_params(
    axis='x',          # changes apply to the x-axis
    which='both',      # both major and minor ticks are affected
    bottom=False,      # ticks along the bottom edge are off
    top=False,         # ticks along the top edge are off
    labelbottom=False)
ax0_.set_xlabel("Players")
ax0_.set_ylabel("Average Change in Cost")
ax1_.tick_params(
    axis='x',          # changes apply to the x-axis
    which='both',      # both major and minor ticks are affected
    bottom=False,      # ticks along the bottom edge are off
    top=False,         # ticks along the top edge are off
    labelbottom=False) 
ax1_.set_xlabel("Players")
ax1_.set_ylabel("Average Change in Cost")
ax0.set_title("Season 1: Same Matchups")
ax1.set_title("Season 2: Same Matchups")
ax0_.set_title("Season 1: Same Pair Used")
ax1_.set_title("Season 2: Same Pair Used")


plt.tight_layout()
plt.show()
