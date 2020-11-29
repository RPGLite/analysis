from shepherd import Shepherd, ShepherdConfig
from tom_models.pdsf import *
from copy import deepcopy, copy
from helper_fns import *
from matplotlib import pyplot as plt
from matplotlib.colors import BASE_COLORS as colours
from matplotlib.colors import TABLEAU_COLORS as colours
from pickle import load, dump
from random import sample, seed, random
from math import log2
from datetime import datetime
from scipy.stats import chisquare, spearmanr, kendalltau
from scipy.optimize import basinhopping, dual_annealing
from numpy import arange
import gc
import sys, os

with AspectHooks():
    from tom_models.base_model import *

season = 1

iteration_num = []
environment = dict()
simulated_choices = list()
correlation = None
best_correlation = None
best_config = None

config = ShepherdConfig()
config.only_season_1 = (season == 1)
config.only_season_2 = (season == 2)
config.remove_developers = True
shepherd = Shepherd(load_cache_by_file=True,
                    config=config)


def change_season(newseason):
    global season, shepherd
    season = newseason
    config = ShepherdConfig()
    config.only_season_1 = (season == 1)
    config.only_season_2 = (season == 2)
    config.remove_developers = True
    shepherd = Shepherd(load_cache_by_file=True,
                        config=config)
    import Constants
    Constants.change_season(season)
    change_modelled_season(season)

change_season(season)


played = 0

# === BEGIN copied and modified from cost_over_skill, which is William's work
# Modified to use shepherd — unused cruft deleted 20201027
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
#=== END copied and modified from cost_over_skill, which is William's work

def generate_simulated_choice_recorder(counts, simulated_choices):
    def record_simulated_choices(target, ret, players, _env, **kwargs):
        global environment, simulated_choices
        completed_game = environment['games'][-1]
        char_pairs = [completed_game[player]['chars'] for player in completed_game['players']]
        char_pairs = map(lambda pair: pair[0].__class__.__name__[0] + pair[1].__class__.__name__[0], char_pairs)
        char_pairs = list(map(lambda pair: pair if pair in counts.keys() else pair[1] + pair[0], char_pairs))
        for pair in char_pairs:
            simulated_choices.append(pair)
    return record_simulated_choices


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

    if list(map(str, gamedoc.get('moves', [None, None])[-2:])) == ['skip', 'skip']:
        return ret

    sorted_moves = sorted(ret.items(), key=lambda move: -move[1])
    return {sorted_moves[0][0]: sorted_moves[0][1]}


def games_played_by(player, _env):
    global environment
    if 'played by' not in environment or player not in environment['played by']:
        return 0
    return environment['played by'][player]
    # return len(list(filter(lambda g: player in g['players'], environment['games'])))


def top_s1_player_usernames_by_games_played(num_players=10):
    games = shepherd.filtered_games()
    counts = dict()
    for game in games:
        counts[game['usernames'][0]] = counts.get(game['usernames'][0], 0) + 1
        counts[game['usernames'][1]] = counts.get(game['usernames'][1], 0) + 1
    sorted_players = sorted(counts.items(), key=lambda kv_pair: -kv_pair[1])
    return list(map(lambda kv_pair: kv_pair[0], sorted_players))[:num_players]

def multiple_iterations_of_simulation_with_config(*args, print_progress=True, iterations=20, rand_seed=0, write_results=True, **kwargs):
    results = list()
    num_iterations = iterations

    seed(rand_seed)
    init_seed = rand_seed * iterations

    for x in range(num_iterations):
        seed(init_seed+x)
        real, res = run_experiment_with_sigmod_parameters(*args, print_progress=print_progress, return_kind="data", **kwargs)
        results.append(res)

    # TODO: write custom kendall-tau
    normalised_char_totals = list(map(lambda x: sum(x)/num_iterations, zip(*results)))

    if write_results:
        with open('corr.txt', 'a') as f:
            f.write(str(args) + "::\t" + str(kendalltau(real, normalised_char_totals)) + "\n")
    return kendalltau(real, normalised_char_totals).pvalue


def run_experiment_with_sigmod_parameters(*args, print_progress=True, return_kind="pval", player_cycle_aggression=0.25, players_to_analyse=None):#simulation_excess, player_count, RGR_control, num real players):
    '''

    Args:
        *args:
        print_progress:
        return_kind: "pval" to return pvalue for correlation, "data" to return tuple(real data, simulated data)
        player_cycle_aggression: a percentage chance of replacing a player with confidence > 0.95

    Returns:

    '''
    global environment, correlation, best_correlation, best_config, simulated_choices
    start = datetime.now()
    simulation_excess, player_count, RGR_control, real_world_players_to_compare = tuple(args[0])
    real_world_players_to_compare = int(real_world_players_to_compare)
    print(tuple(args[0]))
    print("Iteration " + str(len(iteration_num)))
    iteration_num.append(None)

    # simulation_excess = 25
    # player_count = 50
    # RGR_control = 80

    if players_to_analyse is None:
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
    # a = _relative_growth_rate = RGR_control * player_count / len(options) # We want the curve to take roughly len(options) iterations to complete, but this has to be weihted by the number of players getting us to len(options) samples, and the RGR control for annealing.
    k = _upper_asymptote = 1
    a = _relative_growth_rate = RGR_control


    def update_confidence_model(player, _env):

        global environment
        if 'confidence' not in environment: environment['confidence'] = dict()
        y = environment['confidence'].get(player, sigmoid_initial_confidence)
        # BIRCH
        # environment['confidence'][player] = y + a * y * (k - y) / (k - y + c * y)
        # REGULAR LOGISTIC ("Verhulst 1845, 1847")
        environment['confidence'][player] = y + a * y * (1-y)


        return environment['confidence'][player]


    calls = []
    def around_choosing_chars_based_on_sigmoid(next_around, target, _actor, _ctx, _env, **kwargs):
        global environment#, simulated_choices
        calls.append(None)
        update_confidence_model(_actor, environment)
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
        environment['played count'][gamedoc["players"][0]] = environment['played count'].get(gamedoc["players"][0],
                                                                                             0) + 1
        environment['played count'][gamedoc["players"][1]] = environment['played count'].get(gamedoc["players"][0],
                                                                                             0) + 1

        if list(map(str, gamedoc.get('moves', [None, None])[-2:])) == ['skip', 'skip']:
            return ret

        sorted_moves = sorted(ret.items(), key=lambda move: -move[1])
        return {sorted_moves[0][0]: sorted_moves[0][1]}

    def record_simulated_choices(target, ret, players, _env, **kwargs):
        global environment, simulated_choices
        completed_game = environment['games'][-1]
        char_pairs = [completed_game[player]['chars'] for player in completed_game['players']]
        char_pairs = map(lambda pair: pair[0].__class__.__name__[0] + pair[1].__class__.__name__[0], char_pairs)
        char_pairs = list(map(lambda pair: pair if pair in counts.keys() else pair[1] + pair[0], char_pairs))
        for pair in char_pairs:
            simulated_choices.append(pair)


    def record_player_sees_winning_team(target, ret, players, _env, **kwargs):
        global environment
        if 'winning teams' not in environment:
            environment['winning teams'] = dict()

        winning_pair = ""
        for c in environment['games'][-1]["winning player"]:
            winning_pair += c.__class__.__name__[0]

        for actor in players:
            if 'played by' not in environment:
                environment['played by'] = dict()
            environment['played by'][actor] = environment['played by'].get(actor, 0) + 1
            if games_played_by(actor, _env) > initial_exploration:
                environment['winning teams'][actor] = environment['winning teams'].get(actor, list()) + [winning_pair]


    AspectHooks.add_around('choose*', around_choosing_chars_based_on_sigmoid)
    AspectHooks.add_encore('play_game', record_player_sees_winning_team)
    AspectHooks.add_encore('play_game', record_simulated_choices)
    AspectHooks.add_encore('get_moves_from_table', choose_best_moves)

    players = list(range(int(player_count)))
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
            # if len(players) < player_count:
            #     players.append(players[-1]+1)
            players_to_remove = list()
            for player in players:
                if player in environment['confidence'] and environment['confidence'][player] > 0.95 and random() < player_cycle_aggression:
                    players_to_remove.append(player)
            for player in players_to_remove:
                players.append(players[-1]+1)
                players.remove(player)

            # if 'confidence_samples' not in environment: environment['confidence_samples'] = list()
            # environment['confidence_samples'].append(environment['confidence'].get(1, 0.1))
            # plt.plot(list(range(100, 100 * len(environment['confidence_samples'])+1, 100)), environment['confidence_samples'])
            # plt.show()

        try:
            play_game(list(sample(players, 2)), environment)
        except KeyError as e:
            # print("==============\n=============\nHIT KEYERROR\n==========\n==========")
            # print(e)
            err_count += 1
            if str(e).split(',').count('0') < 10:
                raise e
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

    correlation = kendalltau(simulated, observed).pvalue
    try:
        if correlation < best_correlation:
            best_correlation = correlation
            best_config = args
    except:
        best_correlation = correlation
        best_config = args

    AspectHooks.reset()

    gc.collect()  # Run the garbage collector

    if return_kind == "data":
        to_return = (deepcopy(observed), deepcopy(simulated))
    else:
        to_return = kendalltau(simulated, observed).pvalue

        print(kendalltau(simulated, observed).pvalue)

    simulated_choices = list()

    return to_return


sim_start = datetime.now()

def rgr_annealing_multiple_iter_wrapper(rgr, excess=15, player_count=10, real_world_player_count=1, **kwargs):
    args = [[excess, player_count, rgr, real_world_player_count]]
    return multiple_iterations_of_simulation_with_config(*args, **kwargs)

def excess_annealing_multiple_iter_wrapper(excess, player_count=10, rgr=0.2, real_world_player_count=1, **kwargs):
    args = [[excess[0], player_count, rgr, real_world_player_count]]
    return multiple_iterations_of_simulation_with_config(*args, **kwargs)

if __name__ == "__main__":
    # res = list()
    res = dict()
    res[season] = excess_annealing_multiple_iter_wrapper([2])
    change_season(1 if season == 2 else 2)
    res[season] = excess_annealing_multiple_iter_wrapper([2])
    for season, corr in res.items():
        print("season %s: %f.5" % season, corr)
    # print(
    # excess_annealing_multiple_iter_wrapper([90], player_count=30, rgr=0.2, real_world_player_count=1,
    #                                                   players_to_analyse=['Fbomb'], rand_seed=0, iterations=15,
    #                                                   print_progress=True))
    # for excess in range(10, 101, 10):
    #     res.append(excess_annealing_multiple_iter_wrapper([excess], player_count=30, rgr=0.2, real_world_player_count=1, players_to_analyse=['Fbomb'], rand_seed=0, iterations=15, print_progress=True))
    #     plt.plot(list(range(10, 10*len(res)+1, 10)), res)
    #     plt.show()
    # for rgr in arange(0.3, 0.999, 0.05):
    #     res[rgr] = rgr_annealing_multiple_iter_wrapper(rgr, excess=40, player_count=30, real_world_player_count=1, players_to_analyse=['Fbomb'], rand_seed=0, iterations=15, print_progress=True)
    #     plt.plot(res.keys(), res.values())
    #     plt.show()
    # order of args is excess, player count, rgr control, num of real world players
    # print(dual_annealing(partial(rgr_annealing_multiple_iter_wrapper, excess=15, player_count=10, real_world_player_count=1, rand_seed=0, iterations=15, print_progress=True), [[0, 1]], x0=np.array([0.2]), initial_temp=100000, restart_temp_ratio=0.1, maxfun=50, seed=0))  # NOTE: temp has been left at its default
    # print(dual_annealing(partial(excess_annealing_multiple_iter_wrapper, player_count=10, rgr=0.2, real_world_player_count=1, players_to_analyse=['kubajj'], rand_seed=0, iterations=15, print_progress=True), [[1, 150]], x0=np.array([10]), initial_temp=100000, restart_temp_ratio=0.1, maxfun=50, seed=0))  # NOTE: temp has been left at its default
    # for args in [[25.673, 63.783, 70.767, 29.618], [28.856, 88.886, 73.674, 21.649], [43.950, 49.121, 15.909, 16.741], [28.637, 88.637, 64.673, 20.137]]:
    #     for seed_num in range(10):
    #
    #         seed(seed_num)
    #         start = datetime.now()
    #         print("season:\t" + str(season) + "\targs:\t" + str(args) + "\tseed:\t" + str(seed_num) + "\tpval:\t" + str(run_experiment_with_sigmod_parameters(args, print_progress=False)))
    #         end = datetime.now()
    #         print(end-start)

    # results = list()
    # for s in range(1):
    #     # TODO: work out the relationship between the new RGR control for a regular growth curve and the number of players. Think we want to set `a` in the confidence model to something like RGR/player_count, and make this RGR control 0.4. I *think* that replaces actors roughly every 10,000 games, which seems sensible (if frankly quite a lot)
    #     results.append(multiple_iterations_of_simulation_with_config([44.65297373, 23.77786079,  0.97786079,  8.77786079], rand_seed=s, iterations=15, print_progress=True, write_results=False, players_to_analyse=['kubajj']))
    # print(results)

pass
