# September '20 -- let's consider matchups users have seen before. do they get better there?

from helper_fns import *
from bson import objectid
import matplotlib.pyplot as plt
import numpy as np
import math

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
            if m[1] == str(g["usernames"].index(p)+1):
                if m[1] == "1":
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

s1_pair_results = []
p_sqn_ln = []
s1_matchup_results = []
m_sqn_ln = []

first_half = 0
second_half = 0

for season in [1,2]:
    places = []
    matchup_places = []
    for q in db.players.find({"Username":{"$exists":True}}):

        # Remove devs
        if q["Username"] in ["probablytom", "cptKav"]:
            continue
        # Remove those who played fewer than 5 games
        if season == 1:
            played = db.completed_games.count_documents({"winner":{"$exists":True}, "usernames":q["Username"], "balance_code":{"$exists":False}})
        else:
            played = db.completed_games.count_documents({"winner":{"$exists":True}, "usernames":q["Username"], "balance_code":"1.2"})

        if played < 20:
            continue

        matchups,pair_matchups = parse_player_in_season(q["Username"],season)
            
        for p in pair_matchups.keys():
            if len(pair_matchups[p]) >= 10:
                places += [pair_matchups[p].index(max(pair_matchups[p])) / len(pair_matchups[p])]
                p_sqn_ln += [len(pair_matchups[p])]

        for m in matchups.keys():
            if len(matchups[m]) >= 5:
                matchup_places += [matchups[m].index(max(matchups[m])) / len(matchups[m])]
                m_sqn_ln += [len(matchups[m])]


    print("Season {0}, average worst game by pair {1} of {2}, average worst game by matchup {3} of {4} considered".format(
        season, np.average(places), len(places), np.average(matchup_places), len(matchup_places)))
    print("average pair sequence length = {0}, average matchup sequence length = {1}".format(np.average(p_sqn_ln), np.average(m_sqn_ln)))