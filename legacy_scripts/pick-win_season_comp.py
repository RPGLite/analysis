# William Kavanagh

import pymongo
from pprint import pprint
from datetime import date
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

import datetime
from Constants import *
from helper_fns import *
import math

client = pymongo.MongoClient("mongodb://takuu.dcs.gla.ac.uk:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
db = client.Game_data

season1 = db.completed_games.find({"winner": {"$exists": True}, "balance_code":{"$exists":False}}).sort("start_time", pymongo.ASCENDING)
season2 = db.completed_games.find({"winner": {"$exists": True}, "balance_code":{"$exists":True}}).sort("start_time", pymongo.ASCENDING)

def analyse_season(s):
    picked = {}
    won = {}
    for char in chars:
        picked[char] = 0
        won[char] = 0
    for g in s:
        picked[g["p1c1"][0]] += 1
        picked[g["p1c2"][0]] += 1
        picked[g["p2c1"][0]] += 1
        picked[g["p2c2"][0]] += 1
        if g["winner"] == 1:
            won[g["p1c1"][0]] += 1
            won[g["p1c2"][0]] += 1
        else:
            won[g["p2c1"][0]] += 1
            won[g["p2c2"][0]] += 1
    total_played = sum(picked.values())
    print(total_played, "games were played")
    for char in chars:
        print(char, "won", won[char], "games")
        won[char] = ((float(won[char])/float(picked[char]))*100) - 50.0
    for char in chars:
        print(char, "played", picked[char], "games")
        picked[char] = (picked[char] / total_played)
    # print(picked)
    # print(won)
    return picked, won
   

def getImage(path):
    return OffsetImage(plt.imread(path), zoom=.5) 
print("s1:")
s1_p, s1_w = analyse_season(season1)
print("s2:")
s2_p, s2_w = analyse_season(season2)

all_paths = []
for c in chars:
    all_paths += [r"..\analysis\images\square_" + full_name(c).lower() + ".png"]

fig, ax = plt.subplots(nrows=1, ncols=2, figsize = (24,10))
ax.reshape(-1)[0].scatter(s1_p.values(), s1_w.values())
ax.reshape(-1)[0].axhline(y=0.0)
for x0, y0, path in zip(s1_p.values(), s1_w.values(), all_paths):
    ab = AnnotationBbox(getImage(path), (x0, y0),
                        frameon=False, pad=50)
    ax.reshape(-1)[0].add_artist(ab)
ax.reshape(-1)[0].set_title("Season 1")
ax.reshape(-1)[0].axvline(x=0.125)
ax.reshape(-1)[0].set(xlabel="pick rate", ylabel="win delta %")
ax.reshape(-1)[0].set_xlim([0, 0.25])
ax.reshape(-1)[0].set_ylim([-10, 10])
"""
# draw predictions as horizontal lines
count = 0
for pred in [0.4980571429, 0.4161714286, 0.483, 0.4890142857, 0.4953285714, 0.552, 0.5436142857, 0.5228428571]:
    ax.reshape(-1)[0].axhline(y=100*pred-50, linestyle="--", color="green")
    ax.reshape(-1)[0].text(0.125,100*pred-50,chars[count],fontsize=14)
    count+=1
"""

ax.reshape(-1)[1].scatter(s2_p.values(), s2_w.values())
ax.reshape(-1)[1].axhline(y=0.0)
ax.reshape(-1)[1].axvline(x=0.125)
for x0, y0, path in zip(s2_p.values(), s2_w.values(), all_paths):
    ab = AnnotationBbox(getImage(path), (x0, y0),
                        frameon=False, pad=50)
    ax.reshape(-1)[1].add_artist(ab)
ax.reshape(-1)[1].set_title("Season 2")
ax.reshape(-1)[1].set(xlabel="pick rate", ylabel="win delta %")
"""
# draw predictions as horizontal lines for s2
count = 0
for pred in [0.5122285714, 0.4746428571, 0.4824714286, 0.4926, 0.5176, 0.4932, 0.4968857143, 0.5304285714]:
    ax.reshape(-1)[1].axhline(y=100*pred-50, linestyle="--", color="green")
    ax.reshape(-1)[1].text(0.125,100*pred-50,chars[count],fontsize=14)
    count+=1
"""

ax.reshape(-1)[1].set_xlim([0, 0.25])
ax.reshape(-1)[1].set_ylim([-10, 10])


plt.tight_layout() 
plt.show()


