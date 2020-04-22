# Craig asked for this. Turns out he's just bad. #GitGudCraig.

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


def attack_missed(m):
    if "skip" in m or "abandon" in m:
        return True
    if m[2] == "K" and int(m.split("_")[1]) < 100-KNIGHT_ACCURACY:
        return True
    if m[2] == "A":
        if len(m) < 10:
            if int(m.split("_")[1]) < 100-ARCHER_ACCURACY:
                return True
        else:
            if int(m.split("_")[2]) < 100-ARCHER_ACCURACY and int(m.split("_")[1].split("p")[0]) < 100-ARCHER_ACCURACY:
                return True
    if m[2] == "W" and int(m.split("_")[1]) < 100-WIZARD_ACCURACY:
        return True
    if m[2] == "R" and int(m.split("_")[1]) < 100-ROGUE_ACCURACY:
        return True
    if m[2] == "G" and int(m.split("_")[1]) < 100-GUNNER_ACCURACY:
        return True
    if m[2] == "M" and int(m.split("_")[1]) < 100-MONK_ACCURACY:
        return True
    if m[2] == "B" and int(m.split("_")[1]) < 100-BARBARIAN_ACCURACY:
        return True
    if m[2] == "H" and int(m.split("_")[1]) < 100-HEALER_ACCURACY:
        return True
    return False


biggest_streak = 0
streaker = ""
opponent = ""
for g in db.completed_games.find({"winner":{"$exists":True}}):
    p1_s = 0
    p2_s = 0
    p1_worst = 0
    p2_worst = 0
    for m in g["Moves"]:
        if m[1] == "1":
            if attack_missed(m):
                p1_s += 1
            else:
                if p1_s > p1_worst:
                    p1_worst = p1_s
                p1_s = 0
        if m[1] == "2":
            if attack_missed(m):
                p2_s += 1
            else:
                if p2_s > p2_worst:
                    p2_worst = p2_s
                p2_s = 0
    if p1_worst > biggest_streak:
        biggest_streak = p1_worst
        streaker = g["usernames"][0]
        opponent = g["usernames"][1]
    if p2_worst > biggest_streak:
        biggest_streak = p2_worst
        streaker = g["usernames"][1]
        opponent = g["usernames"][0]
    
print("The biggest miss streak in a single game was {0} misses in a row by {1} against {2}".format(biggest_streak, streaker, opponent))

worst = 0
streaker = ""
for u in db.players.find({"Played":{"$gt":0}}):
    streak = 0
    worst_streak = 0
    for e in db.page_hits.find({"user": u["Username"], "kind": "move_viewed", "user_move":"True"}):
        if attack_missed(e["action"]):
            streak += 1
        else:
            if streak > worst_streak:
                worst_streak = streak 
            streak = 0
    if worst_streak > worst:
        streaker = u["Username"]
        worst = worst_streak
    print("{0}'s worst streak was {1} misses".format(u["Username"],worst_streak))
        
print("The biggest miss streak across games was {0} misses in a row by {1}".format(
    worst, streaker))
