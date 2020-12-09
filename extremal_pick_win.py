from helper_fns import *
import matplotlib.pyplot as plt
import numpy as np

s1_data = {}
for pair in pairs:
    s1_data[pair] = {"won":0,"played":0}

# Season 1
for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":{"$exists":False}}):
    p1 = g["p1c1"][0] + g["p1c2"][0]
    if chars.index(p1[1]) < chars.index(p1[0]):
        p1 = p1[1] + p1[0]
    p2 = g["p2c1"][0] + g["p2c2"][0]
    if chars.index(p2[1]) < chars.index(p2[0]):
        p2 = p2[1] + p2[0]
    s1_data[p1]["played"]+=1
    s1_data[p2]["played"]+=1
    if g["winner"] == 1:
        s1_data[p1]["won"]+=1
    else:
        s1_data[p2]["won"]+=1

for p in s1_data.keys():
    s1_data[p]["rate"] = s1_data[p]["won"] / s1_data[p]["played"]


best_pairs = []
# Annotate best pair by rate for each characters
for c in chars:
    best_pair = ""
    for p in pairs:
        if c in p:
            if best_pair == "":
                best_pair = p
            if s1_data[p]["rate"] > s1_data[best_pair]["rate"]:
                best_pair = p
    best_pairs += [best_pair]


plt.scatter(
    [s1_data[p]["played"] for p in s1_data.keys()],
    [s1_data[p]["rate"] for p in s1_data.keys()],
    label=[p for p in s1_data.keys()])

best_pairs += ["WR"]

for p in best_pairs:
    print(p, s1_data[p]["rate"], s1_data[p]["played"])
    plt.annotate(p, xy=(s1_data[p]["played"],s1_data[p]["rate"]), 
    xytext=(s1_data[p]["played"]-50,s1_data[p]["rate"]+0.02),
    arrowprops=dict(arrowstyle="->",connectionstyle="arc3"),
    bbox=dict(boxstyle="round", fc="w"))    

plt.axhline(y=0.5)
plt.xlabel("times chosen")
plt.ylabel("games won (%)")


plt.tight_layout()
plt.show()