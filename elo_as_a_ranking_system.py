# Who is the best player? Can we find out? Let's try.
# Sept 2020

import pymongo
from bson import objectid
from helper_fns import *
import matplotlib.pyplot as plt
import numpy as np
from elo import rate_1vs1

elo = {}

for g in db.completed_games.find({"winner":{"$exists":True}}):
    for u in g["usernames"]:
        if u not in elo:
            elo[u] = 1200
    p1_elo = elo[g["usernames"][0]]
    p2_elo = elo[g["usernames"][1]]

    elo[g["usernames"][0]], elo[g["usernames"][1]] = rate_1vs1(p1_elo, p2_elo)



x = []
y = []

for p in db.players.find({"Played":{"$gt":20}}):
    if p["Username"] in ["cptKav","probablytom","apropos0"]:
        continue
    #print("{0} Played {1} games with a deviance of {2}/action and a total deviance of {3}".format(p["Username"], p["Played"], dev_move, dev))
    x += [elo[p["Username"]]]
    y += [p["Won"]/p["Played"]]
    if elo[p["Username"]] < 1000:
        print(p["Username"])

x = np.array(x, dtype=float)
y = np.array(y, dtype=float)

plt.scatter(x,y)
plt.axhline(y=0.5)
plt.axvline(x=1200)

# best fit
denom = x.dot(x) - x.mean() * x.sum()
m = ( x.dot(y) - y.mean() * x.sum() ) / denom
b = ( y.mean() * x.dot(x) - x.mean() * x.dot(y) ) / denom
y_pred = m*x+b

plt.plot(x, y_pred, "r")
#plt.gca().invert_xaxis()
plt.title("Elo as a ranking")
plt.xlabel("Elo")
plt.ylabel("Win ratio (%)")

print(m, b)

plt.tight_layout()
plt.show()