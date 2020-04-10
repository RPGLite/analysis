# William Kavanagh

from pymongo import MongoClient
from pprint import pprint
from datetime import date
import datetime

client = MongoClient("mongodb://takuu.dcs.gla.ac.uk:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
db = client.Game_data

def analyse_games(games):
    global all_formed, all_malformed
    """Take a list of games and run them numbers.
    played/won stats,
    formed/malformed numbers.
    
    Arguments:
        games {list of completed_game documents} -- [games by day]
    """
    played = {}
    won = {}
    malformed = 0
    formed = 0
    odd = 0
    for g in games:
        # if not "p1c1" in g or not "p2c1" in g or len(g["Moves"]) < 2:
        #     malformed += 1
        #     continue
        # formed += 1
        # if g["p1c1_health"] + g["p1c2_health"] > 0 and g["p2c1_health"] + g["p2c2_health"] > 0:
        #     print(g)
        #     odd += 1
        # for c in [g["p1c1"], g["p1c2"], g["p2c1"], g["p2c2"]]:
        #     if c in played:
        #         played[c] += 1
        #     else:
        #         played[c] = 1
        # if not "winner" in g.keys():
        #     continue
        # if g["winner"] == 1:
        #     for c in [g["p1c1"], g["p1c2"]]:
        #         if c in won:
        #             won[c] += 1
        #         else:
        #             won[c] = 1
        # else:
        #     for c in [g["p2c1"], g["p2c2"]]:
        #         if c in won:
        #             won[c] += 1
        #         else:
        #             won[c] = 1
        if not "winner" in g.keys():
            malformed += 1
        else:
            formed += 1
            if g["winner"]:
                for c in [g["p1c1"], g["p1c2"]]:
                    if c in won:
                        won[c] += 1
                    else:
                        won[c] = 1
            else:
                for c in [g["p2c1"], g["p2c2"]]:
                    if c in won:
                        won[c] += 1
                    else:
                        won[c] = 1
            for c in [g["p1c1"], g["p1c2"], g["p2c1"], g["p2c2"]]:
                if c in played:
                    played[c] += 1
                else:
                    played[c] = 1
        
        
    print()
    for c in played.keys():
        if c not in won.keys():
            won[c] = 0
        print("\t" + c + " played: " + str(played[c]) + ", won: " + \
            str( round(float(won[c]) / float(played[c]) * 100,3)) + "%")
    print("\n\tThere were", str(malformed), "malformed games and", str(formed), "well-formed games.\n")
    all_formed += formed
    all_malformed += malformed

first_day = date(2020,4,3)    # First game was played on this day.
results_by_day = {}
print(db.completed_games.count_documents({"winner": {"$exists": False}}), "games have no winner")
print(db.completed_games.count_documents(
    {"winner": {"$exists": True}}), "do")
all_formed = 0
all_malformed = 0
for g in db.completed_games.find({"start_time": {"$exists": True}}):
    st = g["start_time"].date()
    if abs((first_day-st).days) in results_by_day.keys():
        results_by_day[abs((first_day-st).days)] += [g]
    else:
        results_by_day[abs((first_day-st).days)] = [g]
for d in range(max(results_by_day.keys())+1):
    print("On day", str(d) +":")
    analyse_games(results_by_day[d])
print("In total there were " + str(all_malformed) + " malformed games and " + str(all_formed) + " well-formed games.")
