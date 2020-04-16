# William Kavanagh, April 2020

# Generates pie charts comparing what characters are picked by players have played games in intervals of 5 (i.e.: 0-5, 5-10, 10-15, etc.)

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

client = MongoClient(
    "mongodb://takuu.dcs.gla.ac.uk:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
db = client.Game_data

picks_by_games_played = {}

for u in db.players.find({"Played":{"$gt":4}}):
    # for every user to have played 5 or more games.
    user_games = []
    user = u["Username"]
    for g in db.completed_games.find({"winner": {"$exists": True}, "usernames": user}):
        # for every finished (and formed) game in which they were involved.
        pair = g["p1c1"][0] + g["p1c2"][0] 
        if g["usernames"][0] != u["Username"]:
            pair = g["p2c1"][0]+g["p2c2"][0]
        user_games += [{
            "time": g["start_time"], 
            "pair": pair
        }]
        # add a dictionary for each game to the array of games for that user
    user_games = sorted(user_games, key=lambda i: i['time'])    # sort them by time
    for i in range(len(user_games)):
        if (i+1)%5==0:
            # for every fourth game, add them in
            x = [g["pair"] for g in user_games[i-4:i+1]]
            if i not in picks_by_games_played.keys():        
                picks_by_games_played[i] = [p for p in x]
            else:
                picks_by_games_played[i] += [p for p in x]

for i in picks_by_games_played.keys():
    d = {}
    for c in chars:
        count = 0
        for p in picks_by_games_played[i]:
            if c in p:
                count += 1
        d[c] = count
    picks_by_games_played[i] = d

bars = []

print(picks_by_games_played)

chars = ["K","A","R","H","W","B","M","G"]

plt.figure(figsize=(16, 8))

for c_i in range(len(chars)-1,-1,-1):
    vals = []
    for i in picks_by_games_played.keys():
        vals += [picks_by_games_played[i][chars[c_i][0]] /sum(picks_by_games_played[i].values())]
    if c_i == 7:
        bars += [plt.bar([x-1.5 for x in picks_by_games_played.keys()],
                         vals, 4.8, label=full_name(chars[c_i]))]
        prev_vals = vals
    else:
        bars += [plt.bar([x-1.5 for x in picks_by_games_played.keys()], vals,
                         4.8, bottom=prev_vals, label=full_name(chars[c_i]))]
        prev_vals = [sum(x) for x in zip(prev_vals, vals)]
    print(len([x-1.5 for x in picks_by_games_played.keys()]), len(vals))
plt.legend(loc=1)
plt.xlabel("Games played by player")
plt.ylabel("Proportion of times chosen")
plt.yticks([x*0.125 for x in range(8)])
#plt.xticks([y*5 - 2.5 for y in range(max(picks_by_games_played.keys()))], [str(y-4)+"\nto\n"+str(y+1) for y in picks_by_games_played.keys()])
ax2 = plt.twinx()
line = plt.plot([x-1.5 for x in picks_by_games_played.keys()],
         [sum(picks_by_games_played[x].values()) for x in picks_by_games_played.keys()],
         color="white", label = "# played")
plt.legend(loc=9)

ax2.set_ylabel("Total number of games played")

plt.show()
#print(picks_by_games_played)
