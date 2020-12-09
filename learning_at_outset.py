# William August 2020

import pymongo
from bson import objectid
from helper_fns import *

s1lookup = process_lookup("beta")
s2lookup = process_lookup("tango-2-3")



def check_with_threshold(mistake_treshold, games_to_consider, games_played, first, ignore_first_n):
   
    improved = 0
    regressed = 0
    no_change = 0

    for p in db.players.find({"Username":{"$exists":True}}):

       
        # Ignore players with fewer than X games played.
        if db.completed_games.count_documents({"usernames":p["Username"], "winner":{"$exists":True}}) < games_played:
            continue
        count = 0                       # games considered so far
        mistake_ratios = []             # p(mistake) per game.
        ignored = 0                     # games ignored so far (used for 'second ten' and similar)

        for g in db.completed_games.find({"usernames":p["Username"], "winner":{"$exists":True}}).sort("end_time",1 if first else -1):
                
            if ignored < ignore_first_n:
                #print("game ignored")
                ignored += 1
                continue

            
            count += 1
          
            # ignore dodgy games
            if g["_id"] in [objectid.ObjectId("5e98b4658a225cfc82573fd1"), objectid.ObjectId("5eaaee2c684de5692fc01ef6"), objectid.ObjectId("5ec108ef29108c1ba22cb375")]:    
                #print("dodgy game")
                count -= 1
                continue

            num_mistakes = 0
            num_moves = 0

            # load correct config for game.
            season = 1 if "balance_code" not in g else 2
            if what_config() != season:
                if season == 1:
                    set_config("beta")
                else:
                    set_config("tango-2-3")
            if season == 1:
                lookup = s1lookup
            else:
                lookup = s2lookup

            # setup vars
            pair = g["p1c1"][0] + g["p1c2"][0] if p["Username"] == g["usernames"][0] else g["p2c1"][0] + g["p2c2"][0]
            if chars.index(pair[0]) > chars.index(pair[1]):
                pair = pair[1]+pair[0]
            pos = g["usernames"].index(p["Username"]) + 1
            state = get_initial_state(g)

            # spin over moves
            for m in g["Moves"]:
                if m[1] == str(pos):
                    if pos == 1:
                        if check_actions_available(state, pair, 0.1, lookup):
                            num_moves += 1
                            act, max_poss = cost(state, pair, m, lookup, classify_mistake=True)    # actual P() and maximum possible P()
                            if ((max_poss - act) / max_poss) > mistake_treshold:
                                num_mistakes += 1
                        
                    else:
                        if check_actions_available(flip_state(state), pair, 0.1, lookup):
                            num_moves += 1
                            act, max_poss = cost(flip_state(state), pair, m, lookup, classify_mistake=True)    # actual P() and maximum possible P()
                            if ((max_poss - act) / max_poss) > mistake_treshold:
                                num_mistakes += 1
                        
                do_action(m, state)

            if num_moves > 0 and count > 0:
                mistake_ratios += [num_mistakes/num_moves]
            elif count == 0:
                print("WTF?!")
            else:
                #print(num_moves, g["_id"], "balance_code" in g, "decreasing count")
                count -= 1

            if count > games_to_consider:
                break
        
        if len(mistake_ratios) > games_to_consider/2:
            rolling_avg = [np.mean(mistake_ratios[x:x+3]) for x in range(len(mistake_ratios) - 3)]
            #print(p["Username"], rolling_avg, np.polyfit(range(len(rolling_avg)), rolling_avg, 1)[0])
            #print(p["Username"], rolling_avg)
            grad = np.polyfit(range(len(rolling_avg)), rolling_avg, 1)[0]
            if abs(grad) < 0.0001:
                no_change += 1
            elif grad > 0:
                regressed += 1
            else:
                improved += 1
        #else:
            #print(p["Username"], mistake_ratios)

            #print(rolling_avg)

        #[np.polyfit(range(len(pair_matchups[p])), pair_matchups[p], 1)[0] * len(pair_matchups[p])]
            
    #print("Of the players to have played over {0} games, {1} got better, {2} got worse and {3} didn't change using a {4} mistake threshold.".format(games_to_consider, improved, regressed, no_change, mistake_treshold))

    # print("{0}\t& {1} & {2} ({3}) \t\t{4}, {5} from {6}".format(
    #     games_to_consider, improved + regressed + no_change,
    #     improved/(improved + regressed + no_change), improved/(improved + regressed),
    #     mistake_treshold, "first" if first else "last", games_played
    # ))

    players = improved + regressed + no_change

    return improved/players, improved/(players - no_change), players

"""
out_string = "first 50 & at least 200 & " 
res_string = ""
for Ts in [0.1, 0.2, 0.3, 0.4]:
    imp, imp2, pSum = check_with_threshold(Ts, 50, 200, True, 0)
    res_string += "{:.3f}".format(imp) + " (" + "{:.3f}".format(imp2) + ") & "
out_string += str(pSum) + " & " + res_string[:-3] + " \\\\"
print(out_string)

out_string = "second 50 & at least 200 & " 
res_string = ""
for Ts in [0.1, 0.2, 0.3, 0.4]:
    imp, imp2, pSum = check_with_threshold(Ts, 50, 200, True, 50)
    res_string += "{:.3f}".format(imp) + " (" + "{:.3f}".format(imp2) + ") & "
out_string += str(pSum) + " & " + res_string[:-3] + " \\\\"
print(out_string)

out_string = "third 50 & at least 200 & " 
res_string = ""
for Ts in [0.1, 0.2, 0.3, 0.4]:
    imp, imp2, pSum = check_with_threshold(Ts, 50, 200, True, 100)
    res_string += "{:.3f}".format(imp) + " (" + "{:.3f}".format(imp2) + ") & "
out_string += str(pSum) + " & " + res_string[:-3] + " \\\\"
print(out_string)

"""
out_string = "first 33 & at least 100 & " 
res_string = ""
for Ts in [0.1, 0.2, 0.3, 0.4]:
    imp, imp2, pSum = check_with_threshold(Ts, 33, 100, True, 0)
    res_string += "{:.3f}".format(imp) + " (" + "{:.3f}".format(imp2) + ") & "
out_string += str(pSum) + " & " + res_string[:-3] + " \\\\"
print(out_string)