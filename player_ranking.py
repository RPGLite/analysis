# William Kavanagh

from pymongo import MongoClient
from pprint import pprint
from datetime import date
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import datetime
from Constants import *
from helper_fns import *
import math
from shepherd import *
from bson import objectid


K = 10          # tunable.

s = Shepherd()
players = s.actual_players()

# Function to calculate the Probability
def Probability(rating1, rating2):

    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (rating1 - rating2) / 400))

# Function to calculate Elo rating
# K is a constant.
# d determines whether
# Player A wins or Player B.
# d: did p1 win?
def EloRating(Ra, Rb, K, d):

    # To calculate the Winning
    # Probability of Player B
    Pb = Probability(Ra, Rb)

    # To calculate the Winning
    # Probability of Player A
    Pa = Probability(Rb, Ra)

    # Case -1 When Player A wins
    # Updating the Elo Ratings
    if (d == 1):
        Ra = Ra + K * (1 - Pa)
        Rb = Rb + K * (0 - Pb)

    # Case -2 When Player B wins
    # Updating the Elo Ratings
    else:
        Ra = Ra + K * (0 - Pa)
        Rb = Rb + K * (1 - Pb)

    # print("Updated Ratings:-")
    # print("Ra =", round(Ra, 6), " Rb =", round(Rb, 6))
    return Ra, Rb


rankings = {}
for p in players:
    rankings[p["Username"]] = {"r":1200,"p":0,"w":0}

for g in db.completed_games.find({"winner": {"$exists": True}}):#, "balance_code": {"$exists": False}}):
    p1 = g["usernames"][0]
    p2 = g["usernames"][1]
    if p1 not in rankings or p2 not in rankings:
        continue
    rankings[p1]["p"] += 1
    rankings[p2]["p"] += 1
    d = 1 if g["winner"] == 1 else 2
    if d == 1:
        rankings[p1]["w"] += 1
    else:
        rankings[p2]["w"] += 1
    new_p1_rating, new_p2_rating = EloRating(rankings[p1]["r"], rankings[p2]["r"], K, d)
    rankings[p1]["r"] = new_p1_rating
    rankings[p2]["r"] = new_p2_rating

# data = process_lookup2()
# 
# 
# def flip_state(s):
#     return [1] + s[10:] + s[1:10]
# 
# 
# def find_avg_cost_per_move(user):
#     costs = []
#     mistakes_per_move = []
#     for game in find_games_with_user(user):
#         moves_made = 0
#         mistakes = 0
#         if game["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1"):
#             continue
#         state = get_initial_state(game)
#         user_pair = game["p1c1"][0] + game["p1c2"][0]
#         if game["usernames"].index(user) == 1:
#             user_pair = game["p2c1"][0] + game["p2c2"][0]
#         if chars.index(user_pair[0]) > chars.index(user_pair[1]):
#             user_pair = user_pair[1] + user_pair[0]
#         for m in game["Moves"]:
#             if int(m[1]) - 1 == game["usernames"].index(user):
#                 moves_made += 1
#                 if m[1] == "1":
#                     actual, possible = cost(state, user_pair, m, data, classify_mistake=True)
#                 else:
#                     actual, possible = cost(flip_state(
#                         state), user_pair, m, data, classify_mistake=True)
#                 if possible > 0:
#                     if (possible - actual) / possible > 0.1:
#                         mistakes += 1
#                     costs += [possible-actual]
#             do_action(m, state)
#             if state[0] < 1 or state[0] > 1:
#                 exit
#         if moves_made > 0:
#             mistakes_per_move += [mistakes / moves_made]
#         else:
#             mistakes_per_move += [0]
#     return np.average(costs), np.average(mistakes_per_move) 
# 
# for p in players:
#     rankings[p["Username"]]["c"], rankings[p["Username"]]["m"] = find_avg_cost_per_move(p["Username"])
# 
#     if math.isnan(rankings[p["Username"]]["c"]):
#         rankings.pop(p["Username"])
# 
#     
# 
# # Ra = 1200
# # Rb = 1000
# # d = 1
# # EloRating(Ra, Rb, K, d)
# 
# print(rankings)
