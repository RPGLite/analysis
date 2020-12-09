import pymongo
from bson import objectid
from helper_fns import *
import matplotlib.pyplot as plt
import numpy as np

# s1lookup = process_lookup("beta")
# s2lookup = process_lookup("tango-2-3")

s2_players = []
s1_players = []

for g in db.completed_games.find({"balance_code":"1.2", "winner":{"$exists":True}}):
    for u in g["usernames"]:
        s2_players += [u]

for g in db.completed_games.find({"balance_code":{"$exists":False}, "winner":{"$exists":True}}):
    for u in g["usernames"]:
        s1_players += [u]

s1_pl = []
s2_pl = []

for u in s1_players:
    if s1_players.count(u) > 9 and u not in s1_pl:
        s1_pl += [u]

for u in s2_players:
    if s2_players.count(u) > 9 and u not in s2_pl:
        s2_pl += [u]


sum_s1 = 0
sum_s2 = 0
sum_both = 0

for u in s1_pl:
    if u in s2_pl:
        sum_both += 1
    else:
        sum_s1 += 1
for u in s2_pl:
    if u not in s1_pl:
        sum_s2 += 1

print("both: {0}, s1: {1}, s2: {2}".format(sum_both, sum_s1, sum_s2))