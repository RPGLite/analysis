from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math, pymongo
from bson import objectid

results = np.array([[0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0]])

for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":"1.2"}):
    if g["winner"] == 1:
        results[chars.index(g["p1c1"][0])][chars.index(g["p2c1"][0])] += 1
        results[chars.index(g["p1c1"][0])][chars.index(g["p2c2"][0])] += 1
        results[chars.index(g["p1c2"][0])][chars.index(g["p2c1"][0])] += 1
        results[chars.index(g["p1c2"][0])][chars.index(g["p2c2"][0])] += 1
    else:
        results[chars.index(g["p2c1"][0])][chars.index(g["p1c1"][0])] += 1
        results[chars.index(g["p2c1"][0])][chars.index(g["p1c2"][0])] += 1
        results[chars.index(g["p2c2"][0])][chars.index(g["p1c1"][0])] += 1
        results[chars.index(g["p2c2"][0])][chars.index(g["p1c2"][0])] += 1

ratios = np.array([[.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0]])

for r in range(len(results)):
    for c in range(len(results[r])):
        ratios[r][c] = results[r][c] / (results[r][c] + results[c][r])

fig, (ax,ax2) = plt.subplots(1,2, sharey=True, figsize=(16,10), gridspec_kw={'width_ratios': [3, 1]})
im = ax.imshow(ratios)

ax.set_xticks(np.arange(8))
ax.set_yticks(np.arange(8))
ax.set_yticklabels([full_name(c) for c in chars])
ax.set_xticklabels(chars)

for i in range(8):
    for j in range(8):
        text = ax.text(j, i, "{:.2f}".format(ratios[i, j]),
                       ha="center", va="center", color="w" if ratios[i,j] < 0.51 else "b")

times_played = np.array([[0],[0],[0],[0],[0],[0],[0],[0]])
for c in range(8):
    times_played[c] = [sum(results[c])]

ax.set_title("s2-matchups")
ax2.set_title("s2-times played")

ax2.set_xticks([0])      # turn xticks off for popularity
ax2.set_xticklabels(["# played"])

im2 = ax2.imshow(times_played)
for j in range(8):
        text = ax2.text(0, j, times_played[j, 0],
                       ha="center", va="center", color="w" if times_played[j,0] < np.average([times_played[x][0] for x in range(8)]) else "b")

results = np.array([[0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0],
                    [0,0,0,0,0,0,0,0]])

for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":{"$exists":False}}):
    if g["winner"] == 1:
        results[chars.index(g["p1c1"][0])][chars.index(g["p2c1"][0])] += 1
        results[chars.index(g["p1c1"][0])][chars.index(g["p2c2"][0])] += 1
        results[chars.index(g["p1c2"][0])][chars.index(g["p2c1"][0])] += 1
        results[chars.index(g["p1c2"][0])][chars.index(g["p2c2"][0])] += 1
    else:
        results[chars.index(g["p2c1"][0])][chars.index(g["p1c1"][0])] += 1
        results[chars.index(g["p2c1"][0])][chars.index(g["p1c2"][0])] += 1
        results[chars.index(g["p2c2"][0])][chars.index(g["p1c1"][0])] += 1
        results[chars.index(g["p2c2"][0])][chars.index(g["p1c2"][0])] += 1

ratios = np.array([[.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0],
                    [.0,.0,.0,.0,.0,.0,.0,.0]])

for r in range(len(results)):
    for c in range(len(results[r])):
        ratios[r][c] = results[r][c] / (results[r][c] + results[c][r])

fig2, (_ax,_ax2) = plt.subplots(1,2, sharey=True, figsize=(16,10), gridspec_kw={'width_ratios': [3, 1]})
im = _ax.imshow(ratios)

_ax.set_xticks(np.arange(8))
_ax.set_yticks(np.arange(8))
_ax.set_yticklabels([full_name(c) for c in chars])
_ax.set_xticklabels(chars)

for i in range(8):
    for j in range(8):
        text = _ax.text(j, i, "{:.2f}".format(ratios[i, j]),
                       ha="center", va="center", color="w" if ratios[i,j] < 0.51 else "b")

times_played = np.array([[0],[0],[0],[0],[0],[0],[0],[0]])
for c in range(8):
    times_played[c] = [sum(results[c])]

_ax.set_title("s1-matchups")
_ax2.set_title("s1-times played")

_ax2.set_xticks([0])      # turn xticks off for popularity
_ax2.set_xticklabels(["# played"])

im2 = _ax2.imshow(times_played)
for j in range(8):
        text = _ax2.text(0, j, times_played[j, 0],
                       ha="center", va="center", color="w" if times_played[j,0] < np.average([times_played[x][0] for x in range(8)]) else "b")

plt.tight_layout()

plt.show()