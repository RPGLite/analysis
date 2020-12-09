# August 2020,
# Learning by costs doesn't tell the full story. Costs are heavily dependent on material.
# Check every move made by a player in the same state. How many states like this do you see?

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math, pymongo, copy
from bson import objectid

s1lookup = process_lookup("beta")
s2lookup = process_lookup("tango-2-3")
print()

def plot_player(p, season):

    print("Analysing {0} in season {1}".format(p,season))

    if what_config() != season:
        if season == 1:
            set_config("beta")
        else:
            set_config("tango-2-3")
    if season == 1:
        lookup = s1lookup
        page_hits_query = {"user":p, "kind":"move_viewed", "error":{"$exists":False}, "user_move":"True", "balance_code":{"$exists":False}}
        games_query = {"usernames":p, "winner":{"$exists":True}, "balance_code":{"$exists":False}}
    else:
        lookup = s2lookup
        page_hits_query = {"user":p, "kind":"move_viewed", "error":{"$exists":False}, "user_move":"True", "balance_code":{"$exists":True}}
        games_query = {"usernames":p, "winner":{"$exists":True}, "balance_code":{"$exists":True}}


    state_dictionary = {}
    moves = {}
    notations_seen = []
    count = 0
    for m in db.page_hits.find(page_hits_query):
        moves[count] = m
        count += 1
    costs = {}

    for g in db.completed_games.find(games_query):

        # ignore corrupted games
        if g["_id"] in [objectid.ObjectId("5e98b4658a225cfc82573fd1"), objectid.ObjectId("5eaaee2c684de5692fc01ef6"), objectid.ObjectId("5ec108ef29108c1ba22cb375")]:    
            continue

        # for every game played by p in season 2
        pair = g["p1c1"][0] + g["p1c2"][0] if p == g["usernames"][0] else g["p2c1"][0] + g["p2c2"][0]
        ordered_pair = pair
        if chars.index(pair[0]) > chars.index(pair[1]):
                ordered_pair = pair[1]+pair[0]
        
        opp = g["p2c1"][0] + g["p2c2"][0] if p == g["usernames"][0] else g["p1c1"][0] + g["p1c2"][0]
        move_count = 0
        state = get_initial_state(g)
        for m in g["Moves"]:
            new_state = copy.deepcopy(state)
            do_action(m,new_state)
            num_found = 0
            move_count+=1
            uc1_health = str(new_state[1+(9*g["usernames"].index(p))+chars.index(pair[0])])
            uc2_health = str(new_state[1+(9*g["usernames"].index(p))+chars.index(pair[1])])
            oc1_health = str(new_state[10-(9*g["usernames"].index(p))+chars.index(opp[0])])
            oc2_health = str(new_state[10-(9*g["usernames"].index(p))+chars.index(opp[1])])

            # find the correct move position
            good_log = {}
            for move_log in moves.values():
                if move_log["move_count"] == str(move_count) and move_log["action"] == m and move_log["uc1"] == pair[0] and move_log["uc2"] == pair[1] and move_log["oc1"] == opp[0] and \
                move_log["oc2"] == opp[1] and move_log["uc1_health"] == uc1_health and move_log["uc2_health"] == uc2_health and move_log["oc1_health"] == oc1_health and move_log["oc2_health"] == oc2_health and \
                move_log["time"] > g["start_time"] and move_log["time"] < g["end_time"]:
                    good_log = move_log
                    num_found+=1

            if g["usernames"].index(p) == 1:
                state = flip_state(state)

            if num_found > 3:
                blah = 0
                #print("clash:",g,m)
            elif check_actions_available(state, ordered_pair, 0.15, lookup) and num_found > 0:
                actual, possible = cost(state,ordered_pair,m, lookup,classify_mistake=True)
                costs[good_log["time"]] = (possible-actual) / possible
                if str(state) in state_dictionary.keys():
                    state_dictionary[str(state)] += [(possible-actual) / possible]
                else:
                    state_dictionary[str(state)] = [(possible-actual) / possible]

            state = new_state

    got_worse = 0
    got_better = 0
    no_change = 0
    all_optimal = 0
    repeated_mistake = 0
    grads = []
    for k in state_dictionary.keys():
        if len(state_dictionary[k]) > 1 and state_dictionary[k][0] > 0:
            grad = np.polyfit(range(len(state_dictionary[k])), state_dictionary[k], 1)[0]
            grads += [grad]
            #print(state_dictionary[k], grad)
            if state_dictionary[k].count(0) == len(state_dictionary[k]):
                all_optimal += 1
                #print("all optimal")
            elif state_dictionary[k].count(state_dictionary[k][0]) == len(state_dictionary[k]) and state_dictionary[k][0] != 0:
                repeated_mistake += 1
                #print("repeated mistake")

            if grad < 0.001 and grad > -0.001:
                #print("no change")

                no_change += 1
            elif grad > 0:
                #print("worse")

                got_worse += 1
            else:
                #print("better")

                got_better += 1
    print("{0} states were seen multiple times, in {1} the player improved, in {2} they got worse. In {3} they made the same mistake every time.".format(got_worse+got_better+no_change, got_better, got_worse, repeated_mistake, no_change))
    
    results = [costs[t] for t in sorted(costs.keys())]
    # ordered_critical_costs = [costs[t] for t in res]
    # res = [np.mean(l) for l in np.array_split(ordered_critical_costs, 15)]
    # plt.scatter(range(len(res)),res,label=p)
    x = [x/len(results) for x in range(len(results))]
    

    
    #NEWprint("{0} critical moves were made, {1} were optimal\n".format(len(results),results.count(0)))
    
    
    #plt.scatter(x, results, label = "{0}:{1}".format(p,str(season)))

    # #x = [x/len(res) for x in range(len(res))]
    # x = range(len(res))
    # poly = np.poly1d(np.polyfit(x,res,2))
    # #poly = np.poly1d(np.polyfit(x,ordered_critical_costs,1))
    # x = np.linspace(0,14)
    # y = poly(x)
    # plt.plot(x,y, label=p)
    return np.mean(grads) #NEWgot_better / (got_better + got_worse) if got_better + got_worse > 0 else 0.5

# Find top 10 players in either season
s1players = {}
s2players = {}
for p in db.players.find({"Username":{"$exists":True}}):
    if p["Username"] not in ["apropos0", "cptKav", "probablytom"]:
        s1players[p["Username"]] = db.completed_games.count_documents({"winner":{"$exists":True}, "usernames":p["Username"], "balance_code":{"$exists":False}})
        s2players[p["Username"]] = db.completed_games.count_documents({"winner":{"$exists":True}, "usernames":p["Username"], "balance_code":{"$exists":True}})
s1players = {k:v for k, v in sorted(s1players.items(), key=lambda x: x[1], reverse=True)}
s2players = {k:v for k, v in sorted(s2players.items(), key=lambda x: x[1], reverse=True)}


num_players = 20            # TUNABLE


count = 0
gradients = []
for p in s1players.keys():
    if count >= num_players:
        break
    gradients += [plot_player(p,1)]
    count+=1

# print(gradients)

# for g in gradients:
#     ax0.plot(["start","end"],[0,g], alpha=0.25)
# ax0.plot(["start","end"],[0,np.mean(gradients)])
# s1avg = np.mean(gradients)
# ax0.plot(["start","end"],[0,np.mean(gradients)], color="black", lw=2)
# ax0.axhline(y=0, linestyle=(0, (5, 5)))
# ax0.set_title("Season 1")
# ax0.set_xlabel("Average change over time at repeated states")
# ax0.set_ylabel("Change in Relative Cost")

count = 0
gradients = []
for p in s2players.keys():
    if count >= num_players:
        break
    gradients += [plot_player(p,2)]
    count+=1

# print(gradients)

# for g in gradients:
#    # ax1.plot(["start","end"],[0,g], alpha=0.25)
# ax1.plot(["start","end"],[0,np.mean(gradients)], color="black", lw=2)
# ax1.axhline(y=0, linestyle=(0, (5, 5)))
# ax1.set_title("Season 2")
# ax1.set_xlabel("Average change over time at repeated states")

# print("In season 1 the average gradient is {0}, in season 2 it is {1}".format(s1avg, np.mean(gradients)))

# plt.tight_layout()
# plt.show()

# count = 0
# improved_ratios = []
# for p in s1players.keys():
#     if count < num_players:
#         improved_ratios += [plot_player(p,1)]
#     elif count >= num_players:
#         break
#     count+=1

# print("Of {0} players in season 1, {1} got better".format(num_players, [x>0.5 for x in improved_ratios].count(True)))

# improved_ratios = []

# count = 0
# for p in s2players.keys():
#     if count < num_players:
#         improved_ratios += [plot_player(p,2)]
#     elif count >= num_players:
#         break
#     count+=1
    
# print("Of {0} players in season 2, {1} got better".format(num_players, [x>0.5 for x in improved_ratios].count(True)))


# plt.legend()
# plt.tight_layout()
# plt.show()
