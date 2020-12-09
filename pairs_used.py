from helper_fns import *
import matplotlib.pyplot as plt
import numpy as np

data = []

for g in db.completed_games.find({"balance_code":"1.2", "p2c2":{"$exists":True}, "p1c2":{"$exists":True}}):
    p1 = g["p1c1"][0] + g["p1c2"][0]
    if chars.index(p1[0]) > chars.index(p1[1]):
        p1 = p1[1]+p1[0]
    p2 = g["p2c1"][0]+g["p2c2"][0]
    if chars.index(p2[0]) > chars.index(p2[1]):
        p2 = p2[1]+p2[0]
    data += [[p1,p2]]

def count_pairs(l,p):
    count = 0
    for grp in l:
        for e in grp:
            if e == p:
                count+=1
    return count

pair_data = {}
for p in pairs:
    pair_data[p] = []
    for i in range(int(len(data)/50)):
        pair_data[p] += [count_pairs(data[50*i:50*i+49],p)]
            
most_used = ["KA","KA","KA","KA"]
for p in pairs:
    for i in range(4):
        if np.average(pair_data[p]) > np.average(pair_data[most_used[i]]):
            tmp = str(most_used[i])
            most_used[i] = p
            for j in range(i+1,4):
                if np.average(pair_data[tmp]) > np.average(pair_data[most_used[j]]):
                    new_tmp = str(most_used[j])
                    most_used[j] = tmp
                    tmp = new_tmp
            break


for p in pairs:
    if p in most_used:#== "RM" or p == "WR" or p == "HB" or p == "WM":
        plt.plot(pair_data[p], label = p)
for p in pairs:
    if p not in most_used:
        plt.plot(pair_data[p], alpha=0.1)

plt.xticks([0,17.5,35,52.5,70], ["0",int(17.5*50),35*50,int(52.5*50),70*50])

plt.title("Initial: specific material usage")
plt.xlabel("games played")
plt.ylabel("Times chosen in 50 games")
plt.legend()
plt.tight_layout()
plt.show()
