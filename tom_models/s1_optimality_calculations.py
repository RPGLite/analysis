from shepherd import Shepherd, ShepherdConfig
from time import sleep
from pdsf import *
from copy import deepcopy
from helper_fns import *
from matplotlib import pyplot as plt
from matplotlib.colors import BASE_COLORS as colours
from matplotlib.colors import TABLEAU_COLORS as colours
from pickle import load, dump
from random import sample, seed
from math import log2
from datetime import datetime
from scipy.stats import chisquare, spearmanr

seed(0)

with AspectHooks():
    from tom_models.base_model import *

config = ShepherdConfig()
config.only_season_1 = True
config.remove_developers = True
shepherd = Shepherd(load_cache_by_file=True,
                    config=config)


# === BEGIN copied and modified from cost_over_skill, which is William's work (and helper fns too)
# Modified to use shepherd, and give the cost of all moves made
def flip_state(s):
    return [1] + s[10:] + s[1:10]


def process_lookup2():
    """Parses all lookup2 data into a dictionary and returns
    """
    try:
        with open('lookupV2cache.pickle', 'rb') as cachefile:
            return load(cachefile)
    except Exception as e:
        print(e)
        r = {}
        print("Parsing lookups...")
        count = 0.0
        for p in pairs:
            lookup_d = {}
            with open("../lookupV2/" + p + ".txt","r") as f:
                for l in f.readlines():
                    moves = l.split(":{")[1].split("}")[0]
                    lookup_d[l.split(":")[0]] = moves
            r[p] = lookup_d
            count += 1.0

        with open('lookupV2cache.pickle', 'wb') as cachefile:
            dump(r, cachefile)

        return r

lookup_tables = process_lookup2()

def get_costs_for_each_action(username, count_only_nonobvious_moves=True):
    costs = []
    shepherd.config.game_filters.append(lambda game: username in game['usernames'])
    for game in shepherd.filtered_games():
        curr_game_costs = []
        # if game["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1"):
        #     continue
        state = get_initial_state(game)
        user_pair = game["p1c1"][0] + game["p1c2"][0]

        if game["usernames"].index(username) == 1:
            user_pair = game["p2c1"][0] + game["p2c2"][0]
        if chars.index(user_pair[0]) > chars.index(user_pair[1]):
            user_pair = user_pair[1] + user_pair[0]

        for m in game["Moves"]:
            if int(m[1]) - 1 == game["usernames"].index(username) and (is_significant(state) or not count_only_nonobvious_moves):

                if m[1] == "1":
                    curr_game_costs.append(cost(state, user_pair, m, lookup_tables))

                else:
                    curr_game_costs.append(cost(flip_state(state), user_pair, m, lookup_tables))

            do_action(m, state)

            if state[0] < 1 or state[0] > 1:
                pass

        costs.append(curr_game_costs)

    shepherd.config.game_filters.pop()
    return costs
#=== END copied and modified from cost_over_skill, which is William's work

def is_significant(state):
    return 16-(state[1:9]+state[10:-1]).count(0) >= 2

def costs_with_charpair_played(username, count_only_nonobvious_moves=True):
    costs = list()
    pairs = list()
    shepherd.config.game_filters.append(lambda game: username in game['usernames'])

    game_counter = 0
    for game in shepherd.filtered_games():
        costs.append(list())

        # Make the userpair, conforming to William's stringbuilding style
        playerstr = "p1" if game["usernames"][0] == username else "p2"
        user_pair = game[playerstr + "c1"][0] + game[playerstr + "c2"][0]
        if chars.index(user_pair[0]) > chars.index(user_pair[1]):
            user_pair = user_pair[1] + user_pair[0]
        pairs.append(user_pair)

        state = get_initial_state(game)

        # # Get the cost of each move this player made, and add it to the moves in the costs dict
        # for move in game["Moves"]:
        #     if playerstr[1] == move[1] and (count_only_nonobvious_moves or is_significant(state)):
        #
        #         state = flip_state(state) if move[1] == "1" else state
        #         costs[-1].append(cost(state, user_pair, move, lookup_tables))
        #
        #     do_action(move, state)

        for m in game["Moves"]:
            if int(m[1]) - 1 == game["usernames"].index(username) and (is_significant(state) or not count_only_nonobvious_moves):

                if m[1] == "1":
                    costs[-1].append(cost(state, user_pair, m, lookup_tables))

                else:
                    costs[-1].append(cost(flip_state(state), user_pair, m, lookup_tables))

            do_action(m, state)

            if state[0] < 1 or state[0] > 1:
                pass


    shepherd.config.game_filters.pop()
    return costs, pairs


def convert_gamedoc_to_tom_compatible(gamedoc):
    new_gamedoc = deepcopy(gamedoc)

    new_gamedoc['players'] = gamedoc['usernames']
    new_gamedoc[gamedoc['usernames'][0]] = dict()
    new_gamedoc[gamedoc['usernames'][1]] = dict()
    new_gamedoc[gamedoc['usernames'][0]]['chars'] = [gamedoc['p1c1'], gamedoc['p1c2']]
    new_gamedoc[gamedoc['usernames'][1]]['chars'] = [gamedoc['p2c1'], gamedoc['p2c2']]

    return new_gamedoc

def convert_move_to_optimality_table_format(movestring):
    '''
    Takes a move of a form like "p1Hp2Wp1H_15" and converts it to the format William uses in his optimality tables, like
    "H_WH"
    Args:
        movestring:

    Returns:

    '''

    # Skipping is always 'skip' in the tables
    if 'skip' in movestring:
        return 'skip'

    # We're not skipping! OK.
    # The third char is the one being selected.
    char_moving = movestring[2]
    target = movestring[5]
    move_base = char_moving + "_" + target

    possible_class_names = 'KARHWBMG'

    # Special targeting rules for archer or for healer, so their strings are different.
    if char_moving == 'A':
        # We don't know where the second position is; it could be missing, position 10, or position 11. Try them all.
        if len(movestring) < 10:
            # We didn't target a second time; return as a normal movestring.
            return move_base
        elif movestring[10] in possible_class_names:
            second_target = movestring[10]
        elif movestring[11] in possible_class_names:
            second_target = movestring[11]
        return move_base + second_target

    if char_moving == 'H':
        if len(movestring) > 8 and movestring[8] in possible_class_names:
            heal_target = movestring[8]
            return move_base + heal_target
        else:
            # If the healer doesn't pick a heal target, they're parsed like a normal char, so ignore this and return normally.
            return move_base

    # We have a normal move string! Parse it regularly.
    return move_base

def top_s1_player_usernames_by_games_played(num_players=10):
    games = shepherd.filtered_games()
    counts = dict()
    for game in games:
        counts[game['usernames'][0]] = counts.get(game['usernames'][0], 0) + 1
        counts[game['usernames'][1]] = counts.get(game['usernames'][1], 0) + 1
    sorted_players = sorted(counts.items(), key=lambda kv_pair: -kv_pair[1])
    return list(map(lambda kv_pair: kv_pair[0], sorted_players))[:num_players]

def get_games_for_player(username):
    shepherd.config.game_filters.append(lambda game: username in game['usernames'])
    ret = shepherd.filtered_games()
    shepherd.config.game_filters.pop()
    return ret

def list_of_move_costs_for_user(username):
    games = get_games_for_player(username)
    games = map(convert_gamedoc_to_tom_compatible, games)

    for game in games:
        moves = get_moves_from_table(game)


def line_of_best_fit(dependant_var_points, x_vals=None, supply_func=False):
    '''
    Calculates a naive line of best fit for the datapoints.
    Args:
        dependant_var_points: The y values for the values being plotted.
        x_vals: the x values for the dependant variable datapoints supplied, assuming they're not 1...n

    Returns:

    '''

    if x_vals is None:
        x_vals = list(range(1, len(dependant_var_points) + 1))

    xbar = sum(x_vals) / len(x_vals)
    ybar = sum(dependant_var_points) / len(dependant_var_points)
    n = len(x_vals)  # or len(dependant_var_points)

    numer = sum([xi * yi for xi, yi in zip(x_vals, dependant_var_points)]) - n * xbar * ybar
    denum = sum([xi ** 2 for xi in x_vals]) - n * xbar ** 2

    b = numer / denum
    a = ybar - b * xbar

    if supply_func:
        return lambda x: a + b*x

    return a, b


def windowed_entropy(datapoints, window_size=50):
    def prob(x, window):
        return float(window.count(x))/float(len(window))

    ret = list()
    for i in range(len(datapoints)-window_size):
        window = datapoints[i:i+window_size]
        ret.append(-sum(list(map(lambda x: prob(x, window)*log2(prob(x, window)), window))))

    return ret


def moving_average(datapoints, window_size=10):
    return [sum(datapoints[i:i+window_size])/window_size for i in range(len(datapoints)-window_size)]

if __name__ == '__main__':


    analysis_kind = ["simple", "by_char_played", "entropy", "char_bias", "improved char bias", "correlate random char bias", "correlate by proability distribution", "simulate based on exploration sigmoid"][7]
    moving_average_window_size = 20
    most_active_players = top_s1_player_usernames_by_games_played(10)
    print(most_active_players)


    if analysis_kind == "simple":
        costs = {username: get_costs_for_each_action(username, count_only_nonobvious_moves=True) for username in most_active_players}
        costs = {username: list(filter(lambda cs: len(cs) > 0, costlist)) for username, costlist in costs.items()}
        costs = {username: list(map(lambda x: sum(x)/len(x), user_costs)) for username, user_costs in costs.items()}
        # costs = {username: list(map(lambda x: len(x)-x.count(0), user_costs)) for username, user_costs in costs.items()}
        costs = {username: moving_average(cost_measures, window_size=moving_average_window_size) for username, cost_measures in costs.items()}
        print(costs)
        colours = sample(list(colours.values()), len(costs))
        colourcounter = 0
        for name, values in costs.items():
                plt.plot(range(len(values)), values, color=colours[colourcounter], label=name)
                plt.plot(range(1, len(values)+1, 15), list(map(line_of_best_fit(values, supply_func=True), range(1, len(values)+1, 15))), color=colours[colourcounter])
                print(name, colours[colourcounter])
                colourcounter += 1

        plt.legend()
        plt.xlabel("Number of games played (moving average window " + str(moving_average_window_size) + ")")
        plt.ylabel("Number of non-optimal, non-obvious moves made in a given game")
        plt.show()
        print(sum(list(map(lambda x: line_of_best_fit(x)[1], costs.values())))/len(costs))
        pass
    elif analysis_kind == "by_char_played":
        costs = list()
        most_active_players = ['kubajj']
        for username in most_active_players:
            costs.append(costs_with_charpair_played(username, count_only_nonobvious_moves=True))

        char_costs = {char: list() for char in chars}
        for player_costings in costs:
            moves, characters = player_costings
            for i in range(len(characters)):
                move_list, charpair = moves[i], characters[i]
                char_costs[charpair[0]].append(move_list)
                char_costs[charpair[1]].append(move_list)

        char_costs = {char: list(filter(lambda cs: len(cs) > 0, costlist)) for char, costlist in char_costs.items()}
        # char_costs = {char: list(map(lambda x: len(x)-x.count(0), user_costs)) for char, user_costs in char_costs.items()}
        # char_costs = {username: list(map(lambda x: sum(x)/len(x), user_costs)) for username, user_costs in char_costs.items()}
        successes_counter = 0
        for char, mistakes in char_costs.items():
            distances_to_mistakes = list()
            for move_set in mistakes:
                for cost in move_set:
                    successes_counter += 1
                    if cost != 0:
                        distances_to_mistakes.append(successes_counter)
                        successes_counter = 0
            char_costs[char] = distances_to_mistakes

        # char_costs = {char: moving_average(costs, window_size=moving_average_window_size) for char, costs in char_costs.items()}

        char_pmfs = dict()
        for char, dists in char_costs.items():
            sums = list()
            y_unit = float(1)/float(len(dists))
            y = 0
            for x in range(1, len(dists)+1):
                y += y_unit
                sums.append((sum(dists[:x]), y))
            char_pmfs[char] = sums


        colours = sample(list(colours.values()), len(char_costs.keys()))
        colourcounter = 0
        # for char, costs in char_costs.items():
            # plt.plot(range(len(costs)), costs, color=colours[colourcounter], label=char)
            # plt.plot(range(1, len(costs) + 1, 15),
            #          list(map(line_of_best_fit(costs, supply_func=True), range(1, len(costs) + 1, 15))),
            #          color=colours[colourcounter],
            #          label=char)
            # colourcounter += 1
        for char, pmf_points in char_pmfs.items():
            plt.plot(list(map(lambda x: x[0], pmf_points)), list(map(lambda x: x[1], pmf_points)), color=colours[colourcounter], label=char)
            colourcounter += 1
        plt.legend()
        plt.xlabel("Total moves played with character involved in pair")
        plt.ylabel("Average non-obvious optimal moves in a row")
        plt.show()

    elif analysis_kind == "entropy":
        users_to_analyse = top_s1_player_usernames_by_games_played(5)
        users_to_analyse = ['Jamie']
        interested_in_game = lambda g: g['usernames'][0] in users_to_analyse or g['usernames'][1] in users_to_analyse
        shepherd.config.game_filters.append(interested_in_game)
        games = shepherd.filtered_games()
        shepherd.config.game_filters.pop()

        charpairs = dict()
        for game in games:
            if game['usernames'][0] in users_to_analyse:
                charpairs[game['usernames'][0]] = charpairs.get(game['usernames'][0], list()) + [game['p1c1'][0], game['p1c2'][0]]
            if game['usernames'][1] in users_to_analyse:
                charpairs[game['usernames'][1]] = charpairs.get(game['usernames'][1], list()) + [game['p2c1'][0], game['p2c2'][0]]

        colours=sample(list(colours.values()), len(charpairs.keys()))
        colourcounter = 0

        for player, choices in charpairs.items():
            entropy_values = windowed_entropy(choices, window_size=75)
            plt.plot(list(range(1, len(entropy_values)+1)), entropy_values, color=colours[colourcounter], label=player)
            plt.plot(range(1, len(entropy_values) + 1, 15),
                     list(map(line_of_best_fit(entropy_values, supply_func=True), range(1, len(entropy_values) + 1, 15))),
                     color=colours[colourcounter])
            colourcounter += 1

        plt.legend()
        plt.show()

    if analysis_kind == "char_bias":
        char_to_analyse = "Wizard"
        users_to_analyse = ["tanini"]
        chi_table = list()

        def player_won_with_char(user, allow_opp_win_with_char=False):
            def _(game):

                playerstring = None
                if game['usernames'][0] == user:
                    playerstring = "1"
                elif game['usernames'][1] == user:
                    playerstring = "2"
                else:
                    raise Exception("Filtered user did not play this game...!")

                if allow_opp_win_with_char:
                    chars = [game['p1c1'], game['p1c2'], game['p2c1'], game['p2c2']]
                else:
                    chars = [game['p' + playerstring + 'c1'], game['p' + playerstring + 'c2']]

                return char_to_analyse in chars and (allow_opp_win_with_char or game['winner'] == int(playerstring))

            return _

        shepherd.config.game_filters.append(lambda game: game['usernames'][0] in users_to_analyse or game['usernames'][1] in users_to_analyse)
        # [shepherd.config.game_filters.append(player_won_with_char(player)) for player in users_to_analyse]

        player_games = shepherd.filtered_games()
        player_games = list(sorted(player_games, key=lambda g: datetime.now()-g['start_time']))
        count_won_games = 15

        games_user_won_with_char = list(filter(player_won_with_char(users_to_analyse[0]), player_games))
        for won_game in sample(games_user_won_with_char[:-5], count_won_games):
            char_picked_array = list()

            # Get the five games after the game that was won
            index = player_games.index(won_game)
            for following_game in player_games[index+1:index+6]:

                # Check whether our player picked this game
                playerstring = "1" if following_game['usernames'][0] == users_to_analyse[0] else "2"
                if char_to_analyse in [following_game['p'+playerstring+'c1'], following_game['p'+playerstring+'c2']]:
                    char_picked_array.append(1)
                else:
                    char_picked_array.append(0)

            chi_table.append(char_picked_array)

        def calculate_chi_squared_value(grid):
            total = 0
            for column in grid:
                total += float((sum(column) - 0.25*len(column))**2)/0.25*len(column)
            return total

        def calculate_critical_value(grid):
            return 74.46832416  # 56 degrees of freedom [(5-1)*(15-1)] with a degree of certainty of 0.05


        print(calculate_chi_squared_value(chi_table))
        print(calculate_critical_value(chi_table))
        print(calculate_chi_squared_value(chi_table) < calculate_chi_squared_value(chi_table))



        pass

    elif analysis_kind == "improved char bias":
        players_to_analyse = top_s1_player_usernames_by_games_played(10)
        games_played_collections = dict()  # maps usernames to list of games played, ordered by start time
        chi_table = dict()  # maps usernames to chi squared tables
        expected_table = dict()  # maps usernames to expected value lists
        shepherd.config.game_filters.append(lambda g: g['usernames'][0] in players_to_analyse or g['usernames'][1] in players_to_analyse)
        games = shepherd.filtered_games()

        # Sort games into sets played per player
        for game in list(sorted(games, key=lambda g: datetime.now()-g['start_time'])):
            for user in game['usernames']:
                games_played_collections[user] = games_played_collections.get(user, list()) + [game]

        # Build chi squared for the players we're interested in.
        correlation_depth = 5  # The number of games we look ahead to correlate with.
        for player in players_to_analyse:
            player_games = games_played_collections[player]
            chi_table[player] = list()
            expected_table[player] = list()
            for game_index in range(0, len(player_games)-correlation_depth, correlation_depth):
                hypothesis_val = 0
                expected_val = 0
                playerstring = "1" if game['usernames'][0] == player else "2"
                firstchar = game['p' + playerstring + 'c1']
                secondchar = game['p' + playerstring + 'c2']
                for following_game in player_games[game_index+1:game_index+correlation_depth+1]:

                    # Check whether our player picked this game
                    playerstring = "1" if following_game['usernames'][0] == player else "2"
                    player_won = int(playerstring) == following_game['winner']
                    for char in [firstchar, secondchar]:
                        char_picked = char in [following_game['p' + playerstring + 'c1'],
                                               following_game['p' + playerstring + 'c2']]

                        expected_val += 0.25 if char_picked else 0.75
                        hypothesis_val += 1 if (player_won and char_picked) or (not player_won and not char_picked) else 0

                chi_table[player].append(hypothesis_val)
                expected_table[player].append(expected_val)

            print("For player " + player + ": \t" + str(chisquare(chi_table[player], expected_table[player])))





    if analysis_kind == "correlate random char bias":
        results = list()
        players_to_analyse = top_s1_player_usernames_by_games_played(15)
        games_played_collections = dict()  # maps usernames to list of games played, ordered by start time
        chi_table = dict()  # maps usernames to chi squared tables
        expected_table = dict()  # maps usernames to expected value lists
        shepherd.config.game_filters.append(lambda g: g['usernames'][0] in players_to_analyse or g['usernames'][1] in players_to_analyse)
        games = shepherd.filtered_games()

        # Sort games into sets played per player
        for game in list(sorted(games, key=lambda g: datetime.now()-g['start_time'])):
            for user in game['usernames']:
                games_played_collections[user] = games_played_collections.get(user, list()) + [game]

        # Build chi squared for the players we're interested in.
        correlation_depth = 5  # The number of games we look ahead to correlate with.
        for player in players_to_analyse:
            player_games = games_played_collections[player]
            hypothesis_val, expected_val = [0, 0, 0, 0], [0, 0, 0, 0]
            chi_table[player], expected_table[player] = list(), list()
            won_lost = [0, 0]
            for game_index in range(0, len(player_games)-correlation_depth, correlation_depth):
                playerstring = "1" if game['usernames'][0] == player else "2"
                firstchar = game['p' + playerstring + 'c1']
                secondchar = game['p' + playerstring + 'c2']

                for following_game in player_games[game_index+1:game_index+correlation_depth+1]:

                    playerstring = "1" if following_game['usernames'][0] == player else "2"
                    player_won = int(playerstring) == following_game['winner']
                    won_lost[player_won] += 1
                    for char in [firstchar, secondchar]:
                        char_picked = char in [following_game['p' + playerstring + 'c1'],
                                               following_game['p' + playerstring + 'c2']]

                        # expected_val = [expected_val[0] + 0.25, expected_val[1] + 0.75]
                        # hypothesis_val[0 if char_picked else 1] += 1
                        hypothesis_val[2*char_picked+player_won] += 1

            total_games = sum(won_lost)
            won, lost = won_lost
            expected_val = [
                2*0.75 * total_games,
                2*0.75 * total_games,
                2*0.25 * total_games,
                2*0.25 * total_games
            ]
            print(hypothesis_val)
            print(expected_val)

            print("For player " + player + ": \t" + str(chisquare(hypothesis_val, expected_val)))
            results.append(chisquare(hypothesis_val, expected_val))

        results = list(sorted(results, key=lambda c: c.pvalue))
        print(len(list(filter(lambda c: c.pvalue<0.05, results))))
        print(len(list(filter(lambda c: c.pvalue>0.05, results))))


    if analysis_kind == "correlate by proability distribution":
        results = list()
        players_to_analyse = top_s1_player_usernames_by_games_played(5)
        games_played_collections = dict()  # maps usernames to list of games played, ordered by start time
        chi_table = dict()  # maps usernames to chi squared tables
        expected_table = dict()  # maps usernames to expected value lists
        shepherd.config.game_filters.append(lambda g: g['usernames'][0] in players_to_analyse or g['usernames'][1] in players_to_analyse)
        games = shepherd.filtered_games()

        # Sort games into sets played per player
        for game in list(sorted(games, key=lambda g: datetime.now()-g['start_time'])):
            for user in game['usernames']:
                games_played_collections[user] = games_played_collections.get(user, list()) + [game]

        counts = dict()
        random_counts = dict()
        simulated_counts = dict()
        for i in range(len(chars)):
            for j in range(i + 1, len(chars)):
                counts[chars[i] + chars[j]] = 0
                random_counts[chars[i] + chars[j]] = 0
                simulated_counts[chars[i] + chars[j]] = 0
        for player in players_to_analyse:
            player_games = games_played_collections[player]
            for game in player_games:
                playerstring = "1" if game['usernames'][0] == player else "2"
                firstchar = game['p' + playerstring + 'c1'][0]
                secondchar = game['p' + playerstring + 'c2'][0]

                # Get the ordering consistent using William's char ordering.
                if chars.index(firstchar) > chars.index(secondchar):
                    firstchar, secondchar = secondchar, firstchar

                # Increment the count for the actual games played
                counts[firstchar+secondchar] += 1

                # Increment our random count here, so that by the end we have the same number of games in both counts
                random_counts[choice(list(random_counts.keys()))] += 1



        options = []
        for charpair in counts.keys():
            for _ in range(counts[charpair]):
                options.append(charpair)

        simulated_choices = []
        def pick_chars_by_probability_dist(target, retval, *args, **kwargs):
            # print("picking chars by distribution")
            pair = choice(options)
            simulated_choices.append(pair)
            pair_instances = list()
            char_class_map = {
                "K": Knight,
                "A": Archer,
                "R": Rogue,
                "W": Wizard,
                "H": Healer,
                "B": Barbarian,
                "M": Monk,
                "G": Gunner
            }
            for char in pair:
                pair_instances.append(char_class_map[char]())

            args[1][args[0]]['chars'] = pair_instances
            return pair_instances

        AspectHooks.add_encore('choose_chars', pick_chars_by_probability_dist)

        # TODO: Make a bunch of simulated games, get their distribution, show it correlates with the numbers we picked up.
        simulation_excess = 100
        players = list(range(10))
        env = dict()
        print(len(options) * simulation_excess)
        c = 0
        while len(simulated_choices) < len(options)*simulation_excess:
            c += 1
            print(c)
            try:
                play_game(list(sample(players, 2)), env)
            except KeyError:
                print("==============\n=============\nHIT KEYERROR\n==========\n==========")
                # sleep(1)
            except Exception as e:
                print(e)
                raise e


        # for game in env['games']:
        #     choices = game[game['active player']]['chars']
        #     pair = choices[0].__class__.__name__[0] + choices[1].__class__.__name__[0]
        #     if pair not in counts.keys():
        #         pair = pair[::-1]
        #     simulated_counts[pair] += 1
        for choice in simulated_choices:
            simulated_counts[choice] += 1

        print("counts: " + str(counts))
        print("random_counts: " + str(random_counts))
        print("simulated counts: " + str(simulated_counts))
        observed, expected, simulated = list(), list(), list()
        for key in counts:
            observed.append(counts[key])
            expected.append(random_counts[key])
            simulated.append(simulated_counts[key]/simulation_excess)

        print(sum(observed))
        print(sum(simulated))
        print(sum(expected))

        print(str(chisquare(observed)))
        print(str(chisquare(simulated, observed)))


    elif analysis_kind == "simulate based on exploration sigmoid":
        confidence_points = []
        results = list()
        players_to_analyse = top_s1_player_usernames_by_games_played(5)
        games_played_collections = dict()  # maps usernames to list of games played, ordered by start time
        chi_table = dict()  # maps usernames to chi squared tables
        expected_table = dict()  # maps usernames to expected value lists
        shepherd.config.game_filters.append(lambda g: g['usernames'][0] in players_to_analyse or g['usernames'][1] in players_to_analyse)
        games = shepherd.filtered_games()
        simulated_choices = list()
        env = dict()



        # Sort games into sets played per player
        for game in list(sorted(games, key=lambda g: datetime.now()-g['start_time'])):
            for user in game['usernames']:
                games_played_collections[user] = games_played_collections.get(user, list()) + [game]

        counts = dict()
        random_counts = dict()
        simulated_counts = dict()
        for i in range(len(chars)):
            for j in range(i + 1, len(chars)):
                counts[chars[i] + chars[j]] = 0
                random_counts[chars[i] + chars[j]] = 0
                simulated_counts[chars[i] + chars[j]] = 0
        for player in players_to_analyse:
            player_games = games_played_collections[player]
            for game in player_games:
                playerstring = "1" if game['usernames'][0] == player else "2"
                firstchar = game['p' + playerstring + 'c1'][0]
                secondchar = game['p' + playerstring + 'c2'][0]

                # Get the ordering consistent using William's char ordering.
                if chars.index(firstchar) > chars.index(secondchar):
                    firstchar, secondchar = secondchar, firstchar

                # Increment the count for the actual games played
                counts[firstchar+secondchar] += 1

                # Increment our random count here, so that by the end we have the same number of games in both counts
                random_counts[choice(list(random_counts.keys()))] += 1


        options = []
        for charpair in counts.keys():
            for _ in range(counts[charpair]):
                options.append(charpair)

        simulation_excess = 35
        player_count = 50
        RGR_control = 10

        initial_exploration = 14  # At least a chance to see every pair played.
        sigmoid_initial_confidence = 0.1
        c = _birch_shape_parameter = 1  # 1 for logistic curve
        a = _relative_growth_rate = (RGR_control * player_count) / (simulation_excess * len(options))  # I suppose?
        k = _upper_asymptote = 1


        def games_played_by(player):
            return len(list(filter(lambda g: player in g['players'], env['games'])))


        def confidence_model(player, _env=None):
            if _env is None:
                _env = env

            if 'confidence' not in _env: _env['confidence'] = dict()
            y = _env['confidence'].get(player, sigmoid_initial_confidence)
            _env['confidence'][player] = y + a * y * (k - y) / (k - y + c * y)

            # for graphing the curve
            if player == 2:
                confidence_points.append(env['confidence'][player])

            return games_played_by(player)  # TODO: make this a birch sigmoid representing confidence


        def around_choosing_chars_based_on_sigmoid(next_around, target, _actor, _ctx, _env, **kwargs):


            sigmoid_chose_to_play_winning_pair = random() < confidence_model(_actor, _env)

            if sigmoid_chose_to_play_winning_pair and games_played_by(_actor) > initial_exploration:
                # set winning pair based on the teams they've seen win
                chosen_pair = choice(_env['winning teams'][_actor])
                if chars.index(chosen_pair[0]) > chars.index(chosen_pair[1]):
                    chosen_pair = chosen_pair[1] + chosen_pair[0]
                simulated_choices.append(chosen_pair)
                pair_instances = list()
                char_class_map = {
                    "K": Knight,
                    "A": Archer,
                    "R": Rogue,
                    "W": Wizard,
                    "H": Healer,
                    "B": Barbarian,
                    "M": Monk,
                    "G": Gunner
                }
                for char in chosen_pair:
                    pair_instances.append(char_class_map[char]())

                _ctx[_actor]['chars'] = pair_instances
                return pair_instances
            else:
                ret = next_around(target, _actor, _ctx, _env, **kwargs)
                pair = ""
                for char in _ctx[_actor]['chars']:
                    pair += char.__class__.__name__[0]

                if chars.index(pair[0]) > chars.index(pair[1]):
                    pair = pair[1] + pair[0]
                simulated_choices.append(pair)
                return ret


        def record_player_sees_winning_team(target, ret, players, _env, **kwargs):  # TODO fix signature
            if 'winning teams' not in env:
                env['winning teams'] = dict()

            winning_pair = ""
            for c in _env['games'][-1]["winning player"]:
                winning_pair += c.__class__.__name__[0]

            # if chars.index(winning_pair[0]) > chars.index(winning_pair[1]):
            #     winning_pair = winning_pair[1] + winning_pair[0]
            # simulated_choices.append(winning_pair)

            for actor in players:
                _env['winning teams'][actor] = _env['winning teams'].get(actor, list()) + [winning_pair]


        def choose_best_moves(target, ret, *args, **kwargs):
            '''
            Replaces a set of possible moves from base_model.get_moves_from_table with the single best move, forcing that to be taken.
            Args:
                target: base_model.get_moves_from_table
                ret: the list of best moves to be taken at the game's current state
                *args: args for the function
                **kwargs: keyword args for the function

            Returns: a list containing only the best move of all moves in ret
            '''
            if random() > confidence_model(args[0]['active player'], env) or list(map(str, env['games'][-1]['moves'][-2:])) == ['skip', 'skip']:
                return ret

            sorted_moves = sorted(ret.items(), key=lambda move: -move[1])
            return {sorted_moves[0][0]: sorted_moves[0][1]}


        AspectHooks.add_around('choose_chars', around_choosing_chars_based_on_sigmoid)
        AspectHooks.add_encore('play_game', record_player_sees_winning_team)
        AspectHooks.add_encore('get_moves_from_table', choose_best_moves)


        players = list(range(int(player_count/2)))
        print(len(options) * simulation_excess)
        c = 0
        while len(simulated_choices) < len(options)*simulation_excess:
            c += 1
            print(c)
            if c%100 == 0 and len(players) < player_count:
                players.append(len(players))
            try:
                play_game(list(sample(players, 2)), env)
            except KeyError as e:
                print("==============\n=============\nHIT KEYERROR\n==========\n==========")
                print(e)
                if str(e).split(',').count('0') < 10:
                    raise e
                # sleep(1)
            except Exception as e:
                print(e)
                raise e


        # for game in env['games']:
        #     choices = game[game['active player']]['chars']
        #     pair = choices[0].__class__.__name__[0] + choices[1].__class__.__name__[0]
        #     if pair not in counts.keys():
        #         pair = pair[::-1]
        #     simulated_counts[pair] += 1
        for choice in simulated_choices:
            simulated_counts[choice] += 1

        observed, expected, simulated = list(), list(), list()
        for key in counts:
            observed.append(counts[key])
            expected.append(random_counts[key])
            simulated.append(simulated_counts[key]/simulation_excess)

        print("counts: " + str(counts))
        print("random_counts: " + str(random_counts))
        print("simulated counts: " + str(simulated_counts))
        print()
        print("observed: " + str(observed))
        print("random: " + str(expected))
        print("simulated: " + str(simulated))

        print(str(spearmanr(expected, observed)))
        print(str(spearmanr(simulated, observed)))
        print(str(chisquare(expected, observed)))
        print(str(chisquare(simulated, observed)))

        plt.plot(confidence_points)
        plt.text(len(expected)*0.8, 0.1, 'players: ' + str(player_count) + "\nRGR control: " + str(RGR_control) + "\nsim excess: " + str(simulation_excess) + "\n" + str(spearmanr(simulated, observed)) + '\n' + str(chisquare(simulated, observed)), fontsize=12)
        plt.show()
