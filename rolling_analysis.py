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

first_day = date(2020,4,4)    # First game was played on this day.
results_by_day = {}

for g in db.completed_games.find({"start_time": {"$exists": True}}):
    st = g["start_time"].date()
    if g["start_time"].date() < first_day:
        continue
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
    #print(d)
    for c in chars:
        if d[full_name(c)]["won"] > 0:
            win_delta += [ ((float(d[full_name(c)]["won"]) /
                                float(d[full_name(c)]["played"])) * 100) - 50]
        else:
            win_delta += [50.0]
        if d[full_name(c)]["played"] > 0:
            pick_rate += [float(d[full_name(c)]["played"]) / (d["total"]*4)]
        else:
            pick_rate += [0]
    return pick_rate, win_delta

def getImage(path):
    return OffsetImage(plt.imread(path), zoom=.33)


all_paths = []

for c in chars:
    all_paths += ["images/square_" + full_name(c).lower() + ".png"]

figs_per_row = 4
total_days = max(results_by_day.keys())
rows = math.ceil(total_days/figs_per_row)

fig, ax = plt.subplots(nrows=rows+1, ncols=figs_per_row, figsize=(16,10))

count = 0
for a in ax.reshape(-1):
    paths = all_paths.copy()
    if count <= total_days: # and (count == 9 or count == 10):
        pick_rate, win_delta = plot_pick_win(all_results[count])
        for e in range(len(pick_rate)-1,-1,-1):
            if pick_rate[e]*all_results[count]["total"] < 1:
                pick_rate.pop(e)
                win_delta.pop(e)
                paths.pop(e)
        if(len(pick_rate)<= 0):
            continue
        a.scatter(pick_rate, win_delta)
        for x0, y0, path in zip(pick_rate, win_delta, paths):
            ab=AnnotationBbox(getImage(path), (x0, y0),
                            frameon=False, pad=50)
            a.add_artist(ab)
        a.set_title("day " + str(count + 1) + ", played: " + str(all_results[count]["total"]))
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


for c in chars:
    print("{0} has been played {1} times and has won {2} times".format(
        full_name(c),
        total_results[full_name(c)]["played"],
        total_results[full_name(c)]["won"]))

fig, a = plt.subplots()
pick_rate, win_delta = plot_pick_win(total_results)
a.scatter(pick_rate, win_delta)
for x0, y0, path in zip(pick_rate, win_delta, all_paths):
    ab = AnnotationBbox(getImage(path), (x0, y0),
                        frameon=False, pad=50)
    a.add_artist(ab)
a.axhline(y=0.0)
a.axvline(x=0.125)
a.set(xlabel="pick rate", ylabel="win delta %")
# plt.xlabel('pick rate', fontsize=8)
# plt.ylabel('win delta %', fontsize=8)
a.text(np.max(pick_rate)-0.01, np.max(win_delta)-0.01, "overplayed\ntoo strong", fontsize=8)
a.text(np.max(pick_rate)-0.01, np.min(win_delta), "overplayed\ntoo weak", fontsize=8)
a.text(np.min(pick_rate), np.max(win_delta)-0.01, "underplayed\ntoo strong", fontsize=8)
a.text(np.min(pick_rate), np.min(win_delta), "underplayed\ntoo weak", fontsize=8)

plt.tight_layout()

# # Let's plot some characters!
fig, ax = plt.subplots(nrows=4, ncols=2, sharex='col', sharey='row')
count = 0
for a in ax.reshape(-1):
    char = full_name(chars[count])
    a.set_title(char)
    pick = []
    win = []
    for d in range(total_days):
        pick += [all_results[d][char]["played"] / (all_results[d]["total"]*4)]
        if "won" in all_results[d][char].keys():
            win += [(((all_results[d][char]["won"] / all_results[d][char]["played"]) * 100) - 50)]
        else:
            win += [50]
        if d > 0:
            a.quiver(pick[d-1], win[d-1], pick[d]-pick[d-1], win[d]-win[d-1],
                     angles='xy', scale_units='xy', scale=1, headwidth=3, headlength=5)
    a.scatter(pick,win)
    n = range(total_days)
    a.axhline(y=0.0)
    a.axvline(x=0.125)
    # a.set_xlim([0.05,0.25])
    # a.set_ylim([-15, 15])
    if count > 5:
        a.set(xlabel="pick rate")
    if count % 2 == 0:
        a.set(ylabel="win delta %")
    for i, txt in enumerate(n):
        if i == 0 or i == total_days-1:
            a.annotate(txt, (pick[i], win[i]), fontsize=14)
    count+=1

plt.tight_layout()
plt.show()
