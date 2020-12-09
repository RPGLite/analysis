# William Kavanagh

from pymongo import MongoClient
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



fig, ax = plt.subplots(figsize=(8,6))
games_plot = ax.plot(intervals,totals, "-", label = "Games")
users_plot = ax.plot([],[],"-r",label = "Users")
ax2 = ax.twinx()
ax2.plot(intervals,users, "-r", label = "Users")
ax.legend(loc = 2)
ax.set(ylabel="Games", xlabel="Date")
ax2.set_ylabel("Users")
matts_email = datetime.datetime(2020,4,9,13,00)
ax.axvline(x=matts_email, color="g", dashes = (5,2,1,2))
ax.set(xlabel="Date", ylabel="Games")

def add_30(d):
    return d + datetime.timedelta(minutes=300)

ax.text(add_30(matts_email), 4000,
       "IGDA", fontsize=10)
    
csug = datetime.datetime(2020,4,16,14,00)
ax.axvline(x=csug, color="g", dashes = (5,2,1,2))
ax.text(add_30(csug), 3250,
       "CS UG\nemail", fontsize=10)

ld = datetime.datetime(2020,4,23,17,00)
ax.axvline(x=ld, color="g", dashes = (5,2,1,2))
ax.text(add_30(ld), 1500,
       "UK enters\nlockdown", fontsize=10)

s2 = datetime.datetime(2020,5,4,15,00)
ax.axvline(x=s2, color="g", dashes = (5,2,1,2))
ax.text(add_30(s2),1000,"season 2", fontsize=10)


cose_email = datetime.datetime(2020,5,14,13,00)
ax.axvline(x=cose_email, color="g", dashes = (5,2,1,2))
ax.text(add_30(cose_email), 300,
       "Sci/Eng\nemail", fontsize=10)


ax.xaxis.set_major_locator(mdates.DayLocator(interval=10))   #to get a tick every 15 minutes
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))     #optional formatting
fig.autofmt_xdate()

plt.tight_layout()
plt.show()    
