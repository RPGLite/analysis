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

client = MongoClient(
    "mongodb://takuu.dcs.gla.ac.uk:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
db = client.Game_data

times = []
reg_times = []

for g in db.completed_games.find({"winner":{"$exists":True}}):
    times += [g["start_time"]]
    
for e in db.page_hits.find({"kind":"registration"}):
    reg_times += [e["time"]]
    
comp_time = datetime.datetime(2020,4,4,0,0,0,0,)   
    
intervals = []
totals = []
users = []
count = 0
while comp_time < datetime.datetime.now():
    intervals += [count]
    num_games = 0
    num_users = 0
    for t in times:
        if t < comp_time:
            num_games+=1
    for t in reg_times:
        if t < comp_time:
            num_users += 1  
    totals += [num_games]
    users += [num_users]
    count+=1
    comp_time = comp_time + datetime.timedelta(hours = 1)

for i in range(len(intervals)):
    intervals[i] = datetime.datetime(2020, 4, 4, 0, 0, 0, 0,) + datetime.timedelta(hours=intervals[i])



fig, ax = plt.subplots(figsize=(16,12))
games_plot = ax.plot(intervals,totals, "-", label = "games finished")
users_plot = ax.plot([],[],"-r",label = "users registered")
ax2 = ax.twinx()
ax2.plot(intervals,users, "-r", label = "users registered")
ax.legend(loc = 2)
ax.set(ylabel="completed games", xlabel="date")
ax2.set_ylabel("users")
# matts_email = datetime.datetime(2020,4,9,13,57)
# ax.axvline(x=matts_email)
# ax.set(xlabel="time", ylabel="Number of games completed successfully")
# ax.text(matts_email, 750,
#        "Matt Barr", fontsize=20)
plt.tight_layout()
plt.show()    
