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
from bson import objectid


client = MongoClient(
    "mongodb://takuu.dcs.gla.ac.uk:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
db = client.Game_data


data = process_lookup2()
costs = []
times = []



def flip_state(s):
    return [1] + s[10:] + s[1:10]


for u in db.players.find({"Username": {"$exists": True}, "elo": {"$exists": True}, "Played": {"$gt": 0}}):
    user_events = {}
    user = u["Username"]
    print("{1} moves processed so far. User '{0}' begun.".format(
        user, len(costs)))

    # Parse online game open and move view events:
    for event in db.page_hits.find({"user": user, "kind": "home_to_gameplay"}):
        user_events[event["time"]] = "opened_game"
    for event in db.page_hits.find({"user": user, "kind": "move_viewed"}):
        user_events[event["time"]] = [event["action"], int(event["move_count"])]
    all_times = list(user_events)
    all_times.sort()    # List of the times of all events sorted by time
    
    for game in db.completed_games.find({"winner":{"$exists":True}, "usernames":user}):
        if game["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1"):
            continue 
        #print("Game number {0}:".format(game_num))
        move = 1
        state = get_initial_state(game)
        user_pair = game["p1c1"][0] + game["p1c2"][0]
        if game["usernames"].index(user) == 1:
            user_pair = game["p2c1"][0] + game["p2c2"][0]
        if chars.index(user_pair[0]) > chars.index(user_pair[1]):
            user_pair = user_pair[1] + user_pair[0]
        for m in game["Moves"]:
            if int(m[1])-1 == game["usernames"].index(user):
                # If it was one of the user's turns:
                gen = (x for x in user_events.keys() if x > game["start_time"] and x < game["end_time"] and
                        user_events[x][0] == m and user_events[x][1] == move)
                for e in gen:
                    # This will find the us event that corresponds to having seen this move.
                    index_of_move = all_times.index(e)
                    new_time = e - all_times[index_of_move - 1]
                        
                    break
                    #print(e,m)
                #print("\tmove {0}: {1}".format(move, m))
                if m[1] == "1":
                    new_cost = cost(state, user_pair, m, data)
                else:
                    new_cost = cost(flip_state(state), user_pair, m, data)
                if new_cost != None and new_time != None:
                    costs += [new_cost]
                    times += [new_time]
                else:
                    print(m)
                #print("move {0}, cost {1}, time {2}".format(m,costs[-1],times[-1]))
            do_action(m, state)
            move += 1            
        
        

        
print(len(times), len(costs))
times = [x.total_seconds() for x in times]
for i in range(len(times)-1,-1,-1):
    if times[i] > 120:
        times = times[:i] + times[i+1:]
        costs = costs[:i] + costs[i+1:]
        i-=1
        
plt.scatter(times, costs)
plt.plot(np.unique(times), np.poly1d(np.polyfit(times, costs, 1))(np.unique(times)))

plt.xlabel("time (seconds")
plt.ylabel("cost pWin(outcome) - pWin(highest possible)")
plt.title("cost of move over time (s)")
plt.show()
