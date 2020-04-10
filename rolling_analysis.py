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

client = MongoClient("mongodb://takuu.dcs.gla.ac.uk:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
db = client.Game_data

def analyse_games(games):
    """Take a list of games and run them numbers.
    played/won stats,
    formed/malformed numbers.
    
    Arguments:
        games {list of completed_game documents} -- [games by day]
    """
    day_dictionary = {"total":0}
    for c in chars:
        day_dictionary[full_name(c)] = {"played": 0, "won":0}

    for g in games:
        if "winner" in g.keys():
            day_dictionary["total"] += 1
            if g["winner"]:
                for c in [g["p1c1"], g["p1c2"]]:
                    day_dictionary[c]["won"] += 1
                    # if c in [g["p2c1"], g["p2c2"]]:
                    #     day_dictionary[c]["won"] -= 0.5
            else:
                for c in [g["p2c1"], g["p2c2"]]:
                    day_dictionary[c]["won"] += 1
                    # if c in [g["p1c1"], g["p1c2"]]:
                    #     day_dictionary[c]["won"] -= 0.5
            for c in [g["p1c1"], g["p1c2"], g["p2c1"], g["p2c2"]]:
                day_dictionary[c]["played"] += 1
    return day_dictionary

first_day = date(2020,4,3)    # First game was played on this day.
results_by_day = {}

for g in db.completed_games.find({"start_time": {"$exists": True}}):
    st = g["start_time"].date()
    if abs((first_day-st).days) in results_by_day.keys():
        results_by_day[abs((first_day-st).days)] += [g]
    else:
        results_by_day[abs((first_day-st).days)] = [g]
all_results = {}
total_results = {"total":0}
for c in chars:
    total_results[full_name(c)] = {"played": 0, "won":0}
for d in range(max(results_by_day.keys())+1):
    print("Parsing day {0}.".format(d))
    day_dict = analyse_games(results_by_day[d])
    total_results["total"] += day_dict["total"]
    all_results[d] = day_dict
    for char in chars:
        for attr in ["played", "won"]:
            total_results[full_name(char)][attr] += day_dict[full_name(char)][attr]
    
print(db.completed_games.count_documents(
    {"winner": {"$exists": False}}), "games have no winner")
print(db.completed_games.count_documents(
    {"winner": {"$exists": True}}), "do")


def plot_pick_win(d):
    
    win_delta = []
    pick_rate = []
    for c in chars:
        if d[full_name(c)]["won"] > 0:
            win_delta += [50 - (float(d[full_name(c)]["won"]) /
                                float(d[full_name(c)]["played"])) * 100]
        else:
            win_delta += [50.0]
        if d[full_name(c)]["played"] > 0:
            pick_rate += [float(d[full_name(c)]["played"]) / (d["total"]*4)]
        else:
            pick_rate += [0]
    return pick_rate, win_delta

def getImage(path):
    return OffsetImage(plt.imread(path), zoom=.33)

paths = []

for c in chars:
    paths += ["images/square_" + full_name(c).lower() + ".png"]

figs_per_row = 4
total_days = max(results_by_day.keys())+1
rows = math.ceil(total_days/figs_per_row)

fig, ax = plt.subplots(nrows=rows, ncols=figs_per_row, figsize=(16,8))

count = 0
for a in ax.reshape(-1):
    if count <= total_days:
        pick_rate, win_delta = plot_pick_win(all_results[count])
        print(count, pick_rate)
        a.scatter(pick_rate, win_delta)
        for x0, y0, path in zip(pick_rate, win_delta, paths):
            ab=AnnotationBbox(getImage(path), (x0, y0),
                            frameon=False, pad=50)
            a.add_artist(ab)
        a.set_title("day " + str(count) + ", played: " + str(all_results[count]["total"]))
        a.axhline(y=0.0)
        a.axvline(x=0.125)
        a.set(xlabel="pick rate", ylabel="win delta %")
        # plt.xlabel('pick rate', fontsize=8)
        # plt.ylabel('win delta %', fontsize=8)
        a.text(np.max(pick_rate)-0.01, np.max(win_delta),
                "overplayed\ntoo strong", fontsize=4)
        a.text(np.max(pick_rate)-0.01, np.min(win_delta) -
                0.01, "overplayed\ntoo weak", fontsize=4)
        a.text(np.min(pick_rate)-0.01, np.max(win_delta),
                "underplayed\ntoo strong", fontsize=4)
        a.text(np.min(pick_rate)-0.01, np.min(win_delta)-0.01, "underplayed\ntoo weak", fontsize=4)
    count += 1

plt.tight_layout()
plt.show()


