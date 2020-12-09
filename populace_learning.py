# William
# Generate line graphs for comparison of the average cost of moves comparing player experience and days since release.

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math, pymongo
from bson import objectid
#from scipy.interpolate import make_interp_spline, BSpline


# Some tunable constants
critical_section_delta = 0.1
# End


s1 = process_lookup("beta")
s2 = process_lookup("tango-2-3")

set_config("beta")

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


fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(ncols=2, nrows=2, figsize=(16,12), sharey=True)

def plot_section(min_games, axis):

    games = []
    for i in range(min_games):
        games += [[]]
    users = []

    for p in db.players.find({"Username":{"$exists":True}}):
        if p["Username"] in ["probablytom", "cptKav"]:          # Do not process the devs, they should know better.
            continue
        if db.completed_games.count_documents({"usernames":p["Username"], "winner":{"$exists":True}}) < min_games:
            continue     # Didn't play enough games
        #print("parsing user {0}".format(p["Username"]), end=" ")
        users += [p["Username"]]

        count = 0
        for g in db.completed_games.find({"usernames":p["Username"], "winner":{"$exists":True}}):
            if g["_id"] in [objectid.ObjectId("5e98b4658a225cfc82573fd1"), objectid.ObjectId("5eaaee2c684de5692fc01ef6"), objectid.ObjectId("5ec108ef29108c1ba22cb375")]:        
                continue
            if "balance_code" in g.keys() and what_config() == 1:
                set_config("tango-2-3")
            if "balance_code" not in g.keys() and what_config() == 2:
                set_config("beta")

            ## Play each game, count the costs of the user, add them to the appropriate position.
            costs = get_cost_list(g, p["Username"], s1 if "balance_code" not in g.keys() else s2)
            if len(costs) == 0:
                continue
            try :
                games[count] += [sum(i>0.25 for i in costs) / len(costs)]
            except IndexError:
                print("oops", count)

            count += 1
            if count >= min_games:
                break
            
        #print("count reached {0}".format(count))

    for i in range(len(games)):
        remove_these = []
        for j in range(len(games[i])):
            if math.isnan(games[i][j]):
                remove_these = [j] + remove_these
        for e in remove_these:
            games[i].remove(games[i][e])
        games[i] = np.average(games[i])


    axis.plot(games, 'o')
    x = np.array(range(min_games))
    y = np.array(games)
    m, n, b = np.polyfit(x, y, 2)
    axis.plot(x, m*x*x+n*x+b, '-')
    axis.set_title("minimum games: {0}, players: {1}".format(min_games, len(users)))
    # x_labels = [0]
    # for i in range(min_games):
    #     if i % 10 == 0:
    #         x_labels += [i]
    # axis.set_xticks(np.arange(min_games / len(x_labels)))
    # axis.set_xticklabels(x_labels)
    if axis == ax0 or axis == ax2:
        axis.set_ylabel("Mistakes per move (cost>0.25)")
    axis.set_xlabel("Games")
    print(min_games, np.average(games))

# xnew = np.linspace(0, min_games, min_games*3) 

# spl = make_interp_spline(min_games, games, k=3)  # type: BSpline
# power_smooth = spl(xnew)

# ax.plot(xnew, power_smooth, '-')
plot_section(25, ax0)
plot_section(50, ax1)
plot_section(100, ax2)
plot_section(200, ax3)
#plot_section(400, ax4)

plt.tight_layout()


plt.show()

