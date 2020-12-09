# William
# Generate line graphs for comparison of the average cost of moves comparing player experience and days since release.

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math
from bson import objectid

# Some tunable constants
experience_interval = 20
mistake_value = 0.1
games_played = []
avg_costs = []
proportion_of_mistakes = []

def flip_state(s):
    return [1] + s[10:] + s[1:10]

def process_player(p, games, data, season):
    """
    Take a collection of games (g) and a player username (p)

    return a list of the average costs for the user in each interval
    """
    
    time_and_cost = {}      # dictionary of games played by the user
    time_and_mistakes = {}  
    games_played = 0        # games played by plr

    for g in games:
        if g["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1") or g["_id"] == objectid.ObjectId("5eaaee2c684de5692fc01ef6") or g["_id"] == objectid.ObjectId("5ec108ef29108c1ba22cb375"):    
            # Ignore dodgy game.
            continue
        if p in g["usernames"]:
            if (season == 1 and not "balance_code" in g) or (season == 2 and "balance_code" in g):
                games_played += 1
                total_cost = 0.0
                num_moves = 0
                num_mistakes = 0
                pos = g["usernames"].index(p) + 1
                state = get_initial_state(g)
                pair = g["p1c1"][0] + g["p1c2"][0] if pos else g["p2c1"][0] + g["p2c2"][0]
                if chars.index(pair[0]) > chars.index(pair[1]):
                    pair = pair[1]+pair[0]
                for m in g["Moves"]:
                    if m[1] == str(pos):
                        if pos == 1:
                            act, max_poss = cost(state, pair, m, data, classify_mistake=True)    # actual P() and maximum possible P()
                            if max_poss < 0.9 and max_poss > 0.1 and count_actions_available(state, pair, data) > 2:
                                # if it is a move for the player we are processing
                                num_moves += 1
                                total_cost += ((max_poss - act) / max_poss)
                                if ((max_poss - act) / max_poss) > mistake_value:
                                    num_mistakes += 1
                        else:
                            act, max_poss = cost(flip_state(state), pair, m, data, classify_mistake=True)
                            if max_poss < 0.9 and max_poss > 0.1 and count_actions_available(state, pair, data) > 2:
                                num_moves += 1
                                total_cost += ((max_poss - act) / max_poss)
                                if ((max_poss - act) / max_poss) > mistake_value:
                                    num_mistakes += 1
                    do_action(m, state)
                time_and_cost[g["start_time"]] = total_cost / num_moves if num_moves > 0 else -1
                time_and_mistakes[g["start_time"]] = num_mistakes / num_moves if num_moves > 0 else -1
            else:
                time_and_cost[g["start_time"]] = -1
                time_and_mistakes[g["start_time"]] = -1    

    # Now have dictionary in form {<str> time: <float> average cost, ...}
    ordered_time_and_cost = {k: time_and_cost[k] for k in sorted(time_and_cost)}
    return_list = []
    i = 0
    j = 0
    for elem in ordered_time_and_cost:
        if j == 0:
            return_list += [[ordered_time_and_cost[elem]]]
        else:
            return_list[i] += [ordered_time_and_cost[elem]]
        j+=1
        if j==experience_interval-1:
            j=0
            i+=1
    for i in range(len(return_list)):
        return_list[i] = (sum(return_list[i]) + return_list.count(-1)) / (len(return_list) - return_list.count(-1))

    # Now have dictionary in form {<str> time: <float> average cost, ...}
    ordered_time_and_mistakes = {k: time_and_mistakes[k] for k in sorted(time_and_mistakes)}
    mistakes_return_list = []
    i = 0
    j = 0
    for elem in ordered_time_and_mistakes:
        if j == 0:
            mistakes_return_list += [[ordered_time_and_mistakes[elem]]]
        else:
            mistakes_return_list[i] += [ordered_time_and_mistakes[elem]]
        j+=1
        if j==experience_interval-1:
            j=0
            i+=1
    for i in range(len(mistakes_return_list)):
        mistakes_return_list[i] = (sum(mistakes_return_list[i]) + mistakes_return_list.count(-1)) / (len(mistakes_return_list) - mistakes_return_list.count(-1))

    
    return return_list, mistakes_return_list, games_played

data = process_lookup("tango-2-3")   # start with S1 games
games = db.completed_games.find({"winner":{"$exists":True}, "balance_code":{"$exists":True}})
set_config("tango-2-3")
for p in db.players.find({"Played":{"$gt":0}}):
    p_vals, m_vals, played_count = process_player(p["Username"],games,data,2)
    games_played += [played_count]
    for i in range(len(p_vals)-1):    
        if len(avg_costs) == 0 or i >= len(avg_costs):
            avg_costs += [[p_vals[i]]]
        else:
            avg_costs[i] += [p_vals[i]]
    for i in range(len(m_vals)-1):
        if len(proportion_of_mistakes) == 0 or i >= len(proportion_of_mistakes):
            proportion_of_mistakes += [[m_vals[i]]]
        else:
            proportion_of_mistakes[i] += [m_vals[i]]
    games.rewind()      # RESET THE GAME CURSOR! (this is important, otherwise we pass in an empty collection to process_player)

for i in range(len(avg_costs)):
    avg_costs[i] = np.mean(avg_costs[i])

for i in range(len(proportion_of_mistakes)):
    proportion_of_mistakes[i] = np.mean(proportion_of_mistakes[i])

print(avg_costs)
print(proportion_of_mistakes)

fig, (ax1,ax2,ax3) = plt.subplots(nrows=3, ncols=1)


# graph 1: number of games played.
count_cumulative = [] # f(x)
for i in range(max(games_played)):
    count_cumulative += [sum(num > i for num in games_played)]
    if sum(num > i for num in games_played) < 20:           # Stop caring about buckets with < 20 players.
        break

ax1.plot(count_cumulative)
ax1.set_title("Games played")
ax1.set_xlabel("games")
ax1.set_ylabel("count")

avg_costs = avg_costs[:len(count_cumulative)]

bucket_display = [x*experience_interval for x in range(len(avg_costs))] # x axis
ax2.plot(bucket_display, avg_costs)
ax2.set_title("Average cost of move over {0}-game buckets".format(experience_interval))
ax2.set_xlabel("games played by player")
ax2.set_ylabel("cost (change/possible)")

ax3.plot(proportion_of_mistakes[:len(count_cumulative)])
ax3.set_title("proportion of mistakes (cost > {0}*max possible".format(mistake_value))
ax2.set_xlabel("games played by player")
ax2.set_ylabel("mistakes/all critical moves")

plt.tight_layout()
plt.show()

#data = process_lookup("tango-2-3")  # again for S2

# for all players
    # process the dictionary and add the values to our list

