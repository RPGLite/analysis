from pymongo import MongoClient
from pprint import pprint
from datetime import date
import datetime
import numpy as np
import matplotlib.pyplot as plt
from helper_fns import *

client = MongoClient("mongodb://takuu.dcs.gla.ac.uk:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
db = client.Game_data

def search_by_user(u):
    """
    
    Arguments:
        u {[type]} -- [description]
    """
    rolls = []
    for game in db.completed_games.find({"usernames": {"$exists": True}}):
        if not u in game["usernames"]:
            continue
        p = 2
        if u == game["usernames"][0]:
            p = 1
        for m in game["Moves"]:
            if(m[1] == str(p)):
                # if it is a move our user made.
                for part in m.split("_")[1:]:
                    if "p" in part and not "skip" in part:
                        rolls += [int(part.split("p")[0])]
                    elif "skip" not in part:
                        rolls += [int(part)]
    for game in db.games.find({"usernames": {"$exists": True}}):
        if not u in game["usernames"]:
            continue
        p = 2
        if u == game["usernames"][0]:
            p = 1
        for m in game["Moves"]:
            if(m[1] == str(p)):
                # if it is a move our user made.
                for part in m.split("_")[1:]:
                    if "p" in part and not "skip" in part:
                        rolls += [int(part.split("p")[0])]
                    elif "skip" not in part and "abandon" not in part:
                        rolls += [int(part)]
    #print(rolls)
    return np.mean(rolls)
    
luck_l = []
elo_l = []
for u in db.players.find({"Username":{"$exists": True}, "elo":{"$exists": True}, "Played":{"$gt":0}}):
    # print("User:", u["Username"])
    # print("luck:", search_by_user(u["Username"]))
    # print("ELO:", u["elo"])
    print(u["Username"])
    luck_l += [search_by_user(u["Username"])]
    elo_l += [u["elo"]]            

fig, ax = plt.subplots(figsize=(16,8))
ax.scatter(elo_l, luck_l)
z = np.polyfit(elo_l, luck_l, 1)
p = np.poly1d(z)
plt.plot(elo_l,p(elo_l),"r--")

plt.axvline(x=1200)
plt.axhline(y=49.5)
plt.xlabel("ELO")
plt.ylabel("average roll")
plt.show()

def search_opponent_pair(u1, u2):
    
    print("Games completed between pair:", db.completed_games.count_documents({"usernames": [u1,u2]}) + db.completed_games.count_documents({"usernames": [u2,u1]} ) ) 
    u1_rolls = []
    u2_rolls = []
    for g in db.completed_games.find({"usernames": [u1,u2]}):
        for m in g["Moves"]:
            if m[1] == "1":
                # if it is a move our user made.
                for part in m.split("_")[1:]:
                    if "p" in part and not "skip" in part:
                        u1_rolls += [int(part.split("p")[0])]
                    elif "skip" not in part:
                        u1_rolls += [int(part)]
            else:
                 for part in m.split("_")[1:]:
                    if "p" in part and not "skip" in part:
                        u2_rolls += [int(part.split("p")[0])]
                    elif "skip" not in part:
                        u2_rolls += [int(part)]
    for g in db.completed_games.find({"usernames": [u2,u1]}):
        for m in g["Moves"]:
            if m[1] == "1":
                # if it is a move our user made.
                for part in m.split("_")[1:]:
                    if "p" in part and not "skip" in part:
                        u2_rolls += [int(part.split("p")[0])]
                    elif "skip" not in part:
                        u2_rolls += [int(part)]
            else:
                 for part in m.split("_")[1:]:
                    if "p" in part and not "skip" in part:
                        u1_rolls += [int(part.split("p")[0])]
                    elif "skip" not in part:
                        u1_rolls += [int(part)]
    
    print(u1 + " had an average roll of: " + str(np.average(u1_rolls)))
    print(u2 + " had an average roll of: " + str(np.average(u2_rolls)))
                        
            
    
#print(search_opponent_pair("tanini", "creilly2"))
 
