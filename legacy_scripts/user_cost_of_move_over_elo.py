# WJLKavanagh, April 2020
# RPGLite analysis

# Calculate the average cost of a users moves and plot it over ELO, for all users.

from pymongo import MongoClient
from pprint import pprint
from Constants import *

def cost(state, pair, move):
    return max(looksups[pair].values()) - lookups[pair][move]

# read in lookup table.
def read_in_table(p):
    d = {}
    with open("lookupV2/" + p + ".txt","r") as f:
        for l in f.readlines():
            move_d = {}
            moves = l.split("{")[1].split("}")[0].split(",")
            for m in moves:
                move_d[m.split(":")[0]] = float(m.split(":")[1])
            d[l.split(":")[0]] = move_d
    return d

def process_game(game, p):


def find_cost_per_user(id):
    cost = 0
    for g in games.find( {"p1" : id} ):
        cost += process_game(g, 1)
    for g in games.find( {"p2" : id} ):
        cost += process_game(g, 2)
    return cost

chars = ["K","A","W","R","H","M","B","G"]   # Order determined by lookup tables
pairs = []
for i in range(8):
    for j in range(i+1,8):
        pairs += [chars[i]+chars[j]]
lookups = {}
pairs = ["KA"]
for p in pairs:
    lookups[p] = read_in_table(p)
    print(p + " processed.")

client = MongoClient("mongodb://takuu.dcs.gla.ac.uk:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
db = client.Game_data
games = db.completed_games
for user in db.players.find({"Username":{"$exists":True}}):
    print(user["Username"])
    find_cost_per_user(user["_id"])
    break
