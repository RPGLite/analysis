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

nums = []
plays = []

for i in range(0,600):
    nums += [db.players.count_documents({"Played":{"$gt":i}})]
    plays += [i]

fig, ax = plt.subplots(figsize=(8,3))
ax.set(ylabel="Users", xlabel="Minimum games played")
plt.plot(plays,nums)
plt.tight_layout()
plt.show()    

#print(nums)