from shepherd import Shepherd, ShepherdConfig
from time import sleep
from tom_models.pdsf import *
from copy import deepcopy, copy
from helper_fns import *
from matplotlib import pyplot as plt
from matplotlib.colors import BASE_COLORS as colours
from matplotlib.colors import TABLEAU_COLORS as colours
from pickle import load, dump
from random import sample, seed
from math import log2
from datetime import datetime
from scipy.stats import chisquare, spearmanr
from scipy.optimize import basinhopping, dual_annealing
import gc
import sys, os

with AspectHooks():
    from tom_models.base_model import *

season = 1

config = ShepherdConfig()
config.only_season_1 = (season == 1)
config.only_season_2 = (season == 2)
config.remove_developers = True
shepherd = Shepherd(load_cache_by_file=True,
                    config=config)

played = 0

# === BEGIN copied and modified from cost_over_skill, which is William's work (and helper fns too)
# Modified to use shepherd, and give the cost of all moves made
def flip_state(s):
    return [1] + s[10:] + s[1:10]


def process_lookup2():
    """Parses all lookup2 data into a dictionary and returns
    """
    pickle_filename = 'lookupV2cache_season_' + str(season) + '.pickle'
    try:
        with open(pickle_filename, 'rb') as cachefile:
            return load(cachefile)
    except Exception as e:
        print(e)
        r = {}
        print("Parsing lookups...")
        count = 0.0
        for p in pairs:
            lookup_d = {}
            with open(os.path.abspath(os.getcwd()) + "/../lookupV2/season" + str(season) + "/" + p + ".txt","r") as f:
                for l in f.readlines():
                    moves = l.split(":{")[1].split("}")[0]
                    lookup_d[l.split(":")[0]] = moves
            r[p] = lookup_d
            count += 1.0

        with open(pickle_filename, 'wb') as cachefile:
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

iteration_num = []
environment = dict()
simulated_choices = list()
correlation = None
best_correlation = None
best_config = None


def run_experiment_with_sigmod_parameters(*args, print_progress=True):#simulation_excess, player_count, RGR_control, num real players):
    global environment, correlation, best_correlation, best_config, simulated_choices
    start = datetime.now()
    simulation_excess, player_count, RGR_control, real_world_players_to_compare = tuple(args[0])
    real_world_players_to_compare = int(real_world_players_to_compare)
    print(tuple(args[0]))
    print("Iteration " + str(len(iteration_num)))
    sleep(2)
    iteration_num.append(None)

    # simulation_excess = 25
    # player_count = 50
    # RGR_control = 80

    players_to_analyse = top_s1_player_usernames_by_games_played(real_world_players_to_compare)
    games_played_collections = dict()  # maps usernames to list of games played, ordered by start time
    shepherd.config.game_filters.append(
        lambda g: g['usernames'][0] in players_to_analyse or g['usernames'][1] in players_to_analyse)
    games = shepherd.filtered_games()
    simulated_choices = list()
    # env = {}
    environment = dict()

    # Sort games into sets played per player
    for game in list(sorted(games, key=lambda g: datetime.now() - g['start_time'])):
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
            counts[firstchar + secondchar] += 1

            # Increment our random count here, so that by the end we have the same number of games in both counts
            choice = __import__('random').choice
            random_counts[choice(list(random_counts.keys()))] += 1

    options = []
    for charpair in counts.keys():
        for _ in range(counts[charpair]):
            options.append(charpair)

    initial_exploration = 28*2  # At least a chance to see every pair played. TODO: decide whether initial exploration should be a parameter for the optimiser.
    sigmoid_initial_confidence = 0.1
    c = _birch_shape_parameter = 1  # 1 for logistic curve
    a = _relative_growth_rate = (RGR_control * player_count) / (simulation_excess * len(options))  # I suppose?
    k = _upper_asymptote = 1


    def games_played_by(player, _env):
        global environment
        if 'played by' not in environment or player not in environment['played by']:
            return 0
        return environment['played by'][player]
        # return len(list(filter(lambda g: player in g['players'], environment['games'])))


    def confidence_model(player, _env):

        global environment
        if 'confidence' not in environment: environment['confidence'] = dict()
        y = environment['confidence'].get(player, sigmoid_initial_confidence)
        environment['confidence'][player] = y + a * y * (k - y) / (k - y + c * y)

        return environment['confidence'][player]#games_played_by(player)  # ...TODO: make this a birch sigmoid representing confidence


    calls = []
    def around_choosing_chars_based_on_sigmoid(next_around, target, _actor, _ctx, _env, **kwargs):
        global environment#, simulated_choices
        calls.append(None)
        confidence_model(_actor, environment)
        sigmoid_chose_to_play_winning_pair = random() < environment['confidence'][_actor]
        choice = __import__('random').choice

        if sigmoid_chose_to_play_winning_pair and games_played_by(_actor, environment) > initial_exploration:
            # set winning pair based on the teams they've seen win
            chosen_pair = choice(environment['winning teams'][_actor])
            if chars.index(chosen_pair[0]) > chars.index(chosen_pair[1]):
                chosen_pair = chosen_pair[1] + chosen_pair[0]
            # simulated_choices.append(chosen_pair)
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
            ret = next_around(target, _actor, _ctx, environment, **kwargs)
            pair = ""
            for char in _ctx[_actor]['chars']:
                pair += char.__class__.__name__[0]

            if chars.index(pair[0]) > chars.index(pair[1]):
                pair = pair[1] + pair[0]
            # simulated_choices.append(pair)
            return ret


    def record_player_sees_winning_team(target, ret, players, _env, **kwargs):
        global environment
        if 'winning teams' not in environment:
            environment['winning teams'] = dict()

        winning_pair = ""
        for c in environment['games'][-1]["winning player"]:
            winning_pair += c.__class__.__name__[0]

        # if chars.index(winning_pair[0]) > chars.index(winning_pair[1]):
        #     winning_pair = winning_pair[1] + winning_pair[0]
        # simulated_choices.append(winning_pair)

        for actor in players:
            if 'played by' not in environment:
                environment['played by'] = dict()
            environment['played by'][actor] = environment['played by'].get(actor, 0) + 1
            if games_played_by(actor, _env) > initial_exploration:
                environment['winning teams'][actor] = environment['winning teams'].get(actor, list()) + [winning_pair]

    def record_simulated_choices(target, ret, players, _env, **kwargs):
        global environment, simulated_choices
        completed_game = environment['games'][-1]
        char_pairs = [completed_game[player]['chars'] for player in completed_game['players']]
        char_pairs = map(lambda pair: pair[0].__class__.__name__[0] + pair[1].__class__.__name__[0], char_pairs)
        char_pairs = list(map(lambda pair: pair if pair in counts.keys() else pair[1] + pair[0], char_pairs))
        for pair in char_pairs:
            simulated_choices.append(pair)

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
        global environment
        gamedoc = args[0]
        if 'played count' not in environment:
            environment['played count'] = dict()
        environment['played count'][gamedoc["players"][0]] = environment['played count'].get(gamedoc["players"][0], 0) + 1
        environment['played count'][gamedoc["players"][1]] = environment['played count'].get(gamedoc["players"][0], 0) + 1

        # if 'confidence' not in environment:
        #     confidence_model(gamedoc['players'][0], environment)  # TODO this ABSOLUTELY should not be necessary...?!?!?!??!?!?!?!?!??!?!?!
        #     confidence_model(gamedoc['players'][1], environment)  # TODO this ABSOLUTELY should not be necessary...?!?!?!??!?!?!?!?!??!?!?!

        # if random() > environment['confidence'][gamedoc['active player']] or list(map(str, gamedoc.get('moves', [None, None])[-2:])) == [
        #     'skip', 'skip']:
        if list(map(str, gamedoc.get('moves', [None, None])[-2:])) == ['skip', 'skip']:
            return ret

        sorted_moves = sorted(ret.items(), key=lambda move: -move[1])
        return {sorted_moves[0][0]: sorted_moves[0][1]}

    AspectHooks.add_around('choose*', around_choosing_chars_based_on_sigmoid)
    AspectHooks.add_encore('play_game', record_player_sees_winning_team)
    AspectHooks.add_encore('play_game', record_simulated_choices)
    AspectHooks.add_encore('get_moves_from_table', choose_best_moves)

    players = list(range(int(player_count / 2)))
    print(len(options) * simulation_excess / 2)
    c = 0
    err_count = 0
    last = datetime.now()
    while len(simulated_choices) < len(options) * simulation_excess:
        c += 1
        if c % 100 == 0:
            correlation_string = "" if correlation is None else "\t\tCorrelation:\t" + str(correlation) + "\t\tBest so far:\t" + str(best_correlation) + "\twith config:\t" + str(best_config)
            if print_progress:
                print("Iteration:\t:" + str(len(iteration_num)) + "\t\tGame number:\t" + str(c) + "/" + str(
                round(len(options) * simulation_excess / 2)) + "\t\tArgs passed: \t" + str(tuple(args)) + "\t\tDuration:\t" + str(datetime.now() - start) + "\t\tSeconds per thousand:\t" + str(round((datetime.now()-last).total_seconds()*10, 5)) + correlation_string)
            last = datetime.now()
            if len(players) < player_count:
                players.append(len(players))
        try:
            play_game(list(sample(players, 2)), environment)
        except KeyError as e:
            # print("==============\n=============\nHIT KEYERROR\n==========\n==========")
            # print(e)
            err_count += 1
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
        simulated.append(simulated_counts[key] / simulation_excess)

    global played
    played += 1

    # Cleaning up
    del environment['winning teams']
    del environment['games']
    del environment['confidence']
    del environment['played count']
    del environment['played by']
    # del environment
    environment = dict()
    name = None
    names = locals().keys()
    delstring = ""
    for name in names:
        if name[:2] != "__" and name != "simulated_choices" and name != "best_correlation" and name != "best_config":
            delstring += "del locals()['"+name+"']\n"
    exec(delstring)

    correlation = spearmanr(simulated, observed).pvalue
    try:
        if correlation < best_correlation:
            best_correlation = correlation
            best_config = args
    except:
        best_correlation = correlation
        best_config = args

    AspectHooks.reset()

    gc.collect()  # Run the garbage collector

    simulated_choices = list()

    return spearmanr(simulated, observed).pvalue

sim_start = datetime.now()

if __name__ == "__main__":
    # order of args is excess, player count, rgr control, num of real world players
    print(dual_annealing(run_experiment_with_sigmod_parameters, [[25, 50], [60, 150], [50, 150], [5, 50]], x0=np.array([35, 100, 100, 30]), initial_temp=100000, restart_temp_ratio=0.1, maxfun=50, seed=0))  # NOTE: temp has been left at its default
    # for args in [[25.673, 63.783, 70.767, 29.618], [28.856, 88.886, 73.674, 21.649], [43.950, 49.121, 15.909, 16.741], [28.637, 88.637, 64.673, 20.137]]:
    #     for seed_num in range(10):
    #
    #         seed(seed_num)
    #         start = datetime.now()
    #         print("season:\t" + str(season) + "\targs:\t" + str(args) + "\tseed:\t" + str(seed_num) + "\tpval:\t" + str(run_experiment_with_sigmod_parameters(args, print_progress=False)))
    #         end = datetime.now()
    #         print(end-start)


