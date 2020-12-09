''' 
WKavanagh, June 2020.
Displaying the RPGLite metagame, n games at a time by start date, for both configurations
'''
import pymongo
from pprint import pprint
from datetime import date
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import datetime
from Constants import *
from helper_fns import *
import math
import bisect

n = 75              # TUNABLE


client = pymongo.MongoClient("mongodb://takuu.dcs.gla.ac.uk:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
db = client.Game_data

season1 = db.completed_games.find({"winner": {"$exists": True}, "balance_code":{"$exists":False}}).sort("start_time", pymongo.ASCENDING)
season2 = db.completed_games.find({"winner": {"$exists": True}, "balance_code":{"$exists":True}}).sort("start_time", pymongo.ASCENDING)

s1count = db.completed_games.count_documents({"winner": {"$exists": True}, "balance_code":{"$exists":False}})
s2count = db.completed_games.count_documents({"winner": {"$exists": True}, "balance_code":{"$exists":True}})

s1meta = {}
s2meta = {}



# for i in range(math.floor(s1count/n) + 1):
#     s1meta[i] = pair_dict
# for i in range(math.floor(s2count/n) + 1):
#     s2meta[i] = pair_dict


count = 0
bucket = 0
for g in season1:
    if count == 0:
        pair_dict = {}
        for p in pairs:
            pair_dict[p] = 0
        s2meta[bucket] = pair_dict
    # for every game in season 1 in order of start time
    pair1 = g["p1c1"][0] + g["p1c2"][0]
    pair2 = g["p2c1"][0] + g["p2c2"][0]
    if chars.index(pair1[0]) > chars.index(pair1[1]):
        pair1 = pair1[1]+pair1[0]
    if chars.index(pair2[0]) > chars.index(pair2[1]):
        pair2 = pair2[1]+pair2[0]
    s2meta[bucket][pair1] += 1
    s2meta[bucket][pair2] += 1
    count+=1
    if count == n:
        count = 0
        bucket += 1

print(pair_dict)

val_1 = []
val_2 = []
val_3 = []
id_1 = []
id_2 = []
id_3 = []

s2_meta_display = {}
for i in s2meta.keys():
    s = sum(s2meta[i].values())
    bucketcopy = sorted(s2meta[i], key=s2meta[i].get)
    # print(i)
    # for p in bucketcopy[-3:]:
    #     print("\t" + p + ",", round(s2meta[i][p]/s, 3))
    
    # s2_meta_display[i] = {}
    # for j in range(1,4):
    #     s2_meta_display[i][bucketcopy[-j]] = round(s2meta[i][bucketcopy[-j]]/s, 4) 
    
    val_1 += [round(s2meta[i][bucketcopy[-1]]/s, 4)]
    val_2 += [round(s2meta[i][bucketcopy[-2]]/s, 4)]
    val_3 += [round(s2meta[i][bucketcopy[-3]]/s, 4)]
    id_1 += [bucketcopy[-1]]
    id_2 += [bucketcopy[-2]]
    id_3 += [bucketcopy[-3]]


ind = np.arange(len(val_1))
width = 0.2

print(ind[2])

fig, ax = plt.subplots()

rs1 = ax.bar(ind-width, val_1, width, label = id_1)
rs2 = ax.bar(ind, val_2, width)
rs3 = ax.bar(ind+width, val_3, width)

def autolabel(rects, ids, xoffset, yoffset):
    for i in range(len(rects)):
        height = rects[i].get_height()
        ax.annotate("{}".format(ids[i]),
            xy=(rects[i].get_x() +  xoffset, height + yoffset),
        )
        rects[i].color = "blue"

autolabel(rs1, id_1, -width, 0)
autolabel(rs2, id_2, 0, 0)
autolabel(rs3, id_3, width, -0.005)

plt.show()


#print(s2_meta_display)

# TODO:
    #   1. Plot 28 graphs!
    #   2. Plot a line graph with 28 series