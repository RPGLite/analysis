from shepherd import Shepherd, ShepherdConfig
from multiprocessing.pool import Pool
from multiprocessing import Manager, freeze_support, cpu_count
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from tom_models.pdsf import *
from copy import deepcopy, copy
from helper_fns import *
from matplotlib import pyplot as plt
from matplotlib.colors import BASE_COLORS as colours
from matplotlib.colors import TABLEAU_COLORS as colours
from pickle import load, dump
from random import sample, seed, random
from math import log2, asin, sqrt
from datetime import datetime
from scipy.stats import chisquare, spearmanr, kendalltau
from scipy.optimize import basinhopping, dual_annealing
from numpy import arange
import gc
import sys, os
from memoization import cached

with AspectHooks():
    from tom_models.base_model import *

season = 1

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


config = ShepherdConfig()
config.only_season_1 = (season == 1)
config.only_season_2 = (season == 2)
config.remove_developers = True
shepherd = Shepherd(load_cache_by_file=True,
                    config=config)

# Order matters for comparison's sake, so if the order of a charpair is backwards, we need to swap them.
# We check order by looking up their precendence in the char_ordering dictionary (lowest wins.)
char_ordering = {
    'K': 0,
    'A': 1,
    'W': 2,
    'R': 3,
    'H': 4,
    'M': 5,
    'B': 6,
    'G': 7
}


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

# lookup_tables = process_lookup2()
#=== END copied and modified from cost_over_skill, which is William's work


def convert_gamedoc_to_tom_compatible(gamedoc):
    new_gamedoc = deepcopy(gamedoc)

    new_gamedoc['players'] = gamedoc['usernames']
    new_gamedoc[gamedoc['usernames'][0]] = dict()
    new_gamedoc[gamedoc['usernames'][1]] = dict()
    new_gamedoc[gamedoc['usernames'][0]]['chars'] = [gamedoc['p1c1'], gamedoc['p1c2']]
    new_gamedoc[gamedoc['usernames'][1]]['chars'] = [gamedoc['p2c1'], gamedoc['p2c2']]

    return new_gamedoc


def map_value_generator(env, value_finder):
    vals = []
    def map_value():
        vals.append(value_finder(env))
        plt.plot(vals)
        plt.show()
    return map_value


def games_played_by(player, environment):
    if 'played by' not in environment or player not in environment['played by']:
        return 0
    return environment['played by'][player]
    # return len(list(filter(lambda g: player in g['players'], environment['games'])))


def generate_synthetic_data(rgr_control,
                            iterations,
                            environment,
                            print_progress=False,
                            garbage_collect_intermittently=True,
                            num_synthetic_players=10,
                            sigmoid_initial_confidence=0.1,
                            initial_exploration=28,
                            boredom_confidence=0.98,
                            prob_bored=0.25,
                            sigmoid_used="logistic", # "logistic" for logistic curve, "birch" for birch curve.
                            boredom_period=25,
                            birch_c=1):  # boredom period is probably usefully set as (num players / 2) squared. Means the players have the opportunity to play each other, but we're not waiting forever; it's the area of a half of an adjacency matrix, roughly.

    environment['special vals'] = dict()
    environment['special vals']['rgr'] = rgr_control
    environment['special vals']['sigmoid type'] = sigmoid_used
    environment['special vals']['birch c'] = birch_c

    def update_confidence_model(player, environment):

        # global rgr_control

        if 'confidence' not in environment: environment['confidence'] = dict()
        y = environment['confidence'].get(player, sigmoid_initial_confidence)
        if environment['special vals']['sigmoid type'] == "logistic":
            # REGULAR LOGISTIC ("Verhulst 1845, 1847")
            environment['confidence'][player] = y + ( environment['special vals']['rgr'] * y * (1-y) )
        elif 'birch' in environment['special vals']['sigmoid type']:
            k = 1  # upper asymptote
            a = environment['special vals']['rgr']
            if environment['special vals']['sigmoid type'] == "birch logistic":
                # BIRCH LOGISTIC
                c = 1  # for logistic curve
                environment['confidence'][player] = y + a * y * (k - y) / (k - y + c * y)
            elif environment['special vals']['sigmoid type'] == "birch exponential":
                # BIRCH EXPONENTIAL
                c = 0  # for exponential curve
            elif environment['special vals']['sigmoid type'] == "birch controlled":
                # BIRCH but with the curve value set specifically
                c = environment['special vals']['birch c']
            else:
                # birch, but not specified which one
                raise Exception("Birch equation used, but no specific equation requested")
            # Same equation for any of these
            environment['confidence'][player] = y + a * y * (k - y) / (k - y + c * y)


        return environment['confidence'][player]


    def around_choosing_chars_based_on_sigmoid(next_around, target, _actor, _ctx, environment, **kwargs):
        update_confidence_model(_actor, environment)
        sigmoid_chose_to_play_winning_pair = random() < environment['confidence'][_actor]
        choice = __import__('random').choice

        if sigmoid_chose_to_play_winning_pair and games_played_by(_actor, environment) > initial_exploration:
            # set winning pair based on the teams they've seen win
            chosen_pair = choice(environment['winning teams'][_actor])
            if chars.index(chosen_pair[0]) > chars.index(chosen_pair[1]):
                chosen_pair = chosen_pair[1] + chosen_pair[0]
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
            return ret

    def best_move_generator(environment):
        def choose_best_moves(target, ret, *args, **kwargs):
            '''
            Replaces a set of possible moves from base_model.get_moves_from_table with the single best move, forcing that to be taken.
            Args:
                target: base_model.get_moves_from_table
                ret: the list of best moves to be taken at the game's current state
                *args: args for the function
                **kwargs: keyword args for the function

            Returns: a list containing only the best move of all moves in ret

            Note: environment here is a reference to the outer scoped 'environment' variable as passed into the function containing this func def.
            '''
            gamedoc = args[0]

            if list(map(str, gamedoc.get('moves', [None, None])[-2:])) == ['skip', 'skip']:
                return ret

            sorted_moves = sorted(ret.items(), key=lambda move: -move[1])
            return {sorted_moves[0][0]: sorted_moves[0][1]}
        return choose_best_moves

    def record_simulated_choices(target, ret, players, environment, **kwargs):
        # Get a reference to the simulated choices list, and add it to the environment if it doesn't exist.
        if 'simulated_choices' not in environment:
            environment['simulated_choices'] = list()
        simulated_choices = environment['simulated_choices']

        completed_game = environment['games'][-1]

        # The pairs chosen by the players
        char_pairs = [completed_game[player]['chars'] for player in completed_game['players']]

        # Changing the pairs chosen into two-letter forms as per RPGLite's backend, such as KA for (Knight, Archer) pair
        char_pairs = map(lambda pair: pair[0].__class__.__name__[0] + pair[1].__class__.__name__[0], char_pairs)

        # Order matters for comparison's sake, so if the order is backwards, swap them. We check order by looking up their precendence in the char_ordering dictionary (lowest wins.)
        char_pairs = list(map(lambda pair: pair if char_ordering[pair[0]] < char_ordering[pair[1]] else pair[1] + pair[0], char_pairs))
        for pair in char_pairs:
            simulated_choices.append(pair)


    def record_player_sees_winning_team(target, ret, players, environment, **kwargs):
        if 'winning teams' not in environment:
            environment['winning teams'] = dict()

        winning_pair = ""
        for c in environment['games'][-1]["winning player"]:
            winning_pair += c.__class__.__name__[0]

        for actor in players:
            if 'played by' not in environment:
                environment['played by'] = dict()
            environment['played by'][actor] = environment['played by'].get(actor, 0) + 1
            # if games_played_by(actor, environment) > initial_exploration:
            environment['winning teams'][actor] = environment['winning teams'].get(actor, list()) + [winning_pair]

    def handle_player_cannot_win(_target, exception_raised, player, gamedoc, environment):
        '''
        To be applied as an exception handler on base_model.take_turn.
        A KeyError is raised if no moves are available to the player --- this happens when William has determined that
        there are no possible futures where the player in question can win!
        So, we artificially reduce their health to 0.
        '''
        if isinstance(exception_raised, KeyError) and exception_raised.__repr__().count('0') > 12:
            gamedoc[player]['chars'][0].health = 0
            gamedoc[player]['chars'][1].health = 0
            # Swap the active player so this player "takes another turn" and loses.
            gamedoc['active player'] = get_opponent(gamedoc['active player'], gamedoc, environment)
            return True
        elif isinstance(exception_raised, ValueError):
            pass

    def catchallerrors(*args, **kwargs):
        pass

    rule_removers = list()
    rule_removers.append(AspectHooks.add_around('choose*', around_choosing_chars_based_on_sigmoid))
    rule_removers.append(AspectHooks.add_encore('play_game', record_player_sees_winning_team))
    rule_removers.append(AspectHooks.add_encore('play_game', record_simulated_choices))
    rule_removers.append(AspectHooks.add_encore('get_moves_from_table', best_move_generator(environment)))
    rule_removers.append(AspectHooks.add_error_handler('take_turn', handle_player_cannot_win))
    rule_removers.append(AspectHooks.add_error_handler('play_game', catchallerrors))


    # Our base model is now aspect-applied.
    # From here, we'll produce a pool of synthetic players and simulate games, generating data as we go.
    players = list(range(int(num_synthetic_players / 2)))
    total_players = len(players)

    # Simulation process:
    #   set up a pool of 50% of the total players (default 10), and have them play against each other.
    #   repeatedly play games.
    #   every (num_synthetic_players/2)^2 games (default 10^2), we:
    #     check to see if any players are experienced enough to become bored.
    #       if they are, we remove them with probability prob_bored (a parameter of this function, way up at the top. Default 0.2).
    #     check to see if there's interest from new players i.e. the player pool is not full
    #       if it is, add a new player
    #   stop playing once `iterations` games is reached (a non-optional parameter of this function)

    for game_number in range(iterations):
        # 1. Play the game
        matchup = sample(players, 2)
        try:
            play_game(matchup, environment)
        except:
            pass

        # 2. Every few games, manage playerbase.
        # I think this is usefully set at around (num players / 2) squared.
        # Means the players have the opportunity to play each other, but we're not waiting forever; it's the area of a half of an adjacency matrix, roughly.
        if game_number % boredom_period == 0:

            # Remove bored players
            to_remove = list()
            try:
                for player in players:
                    player_confidence = environment['confidence'].get(player, sigmoid_initial_confidence)
                    if random() < prob_bored and player_confidence > boredom_confidence:
                        to_remove.append(player)
                for player in to_remove:
                    players.remove(player)
            except:
                pass

            # Add new players if there's room
            while len(players) < num_synthetic_players:
                players.append(total_players)
                total_players += 1

            if garbage_collect_intermittently:
                gc.collect()

            # Printing logic can go here.
            if print_progress:
                print("%f.2 (%d), rgr %f.5" % (game_number, iterations, rgr_control))

    for rule_remover in rule_removers:
        AspectHooks.remove(rule_remover)

    # return environment['simulated_choices']

def find_distribution_of_charpairs_for_user_from_gameset(player, gameset):
    charpair_distribution = dict()
    for game in gameset:
        # Game is from RPGLite's real-world mongodb if it has a `_id` field.
        if '_id' in game:
            game = convert_gamedoc_to_tom_compatible(game)

        if player in game:
            char1 = game[player]['chars'][0][0]
            char2 = game[player]['chars'][1][0]
            pair = char1 + char2 if char_ordering[char1] < char_ordering[char2] else char2 + char1

            charpair_distribution[pair] = charpair_distribution.get(pair, 0) + 1

    return charpair_distribution

def find_distribution_of_charpairs_from_players_collective_games(players, gameset):
    distribution = dict()
    for player in players:
        player_distribution = find_distribution_of_charpairs_for_user_from_gameset(player, gameset)
        for charpair, count in player_distribution.items():
            distribution[charpair] = distribution.get(charpair, 0) + count

    return distribution

def compare_with_multiple_players(rgr_control, iterations, players, games=None, season=1, **kwargs):
    # change_season(season)

    environment = dict()

    generate_synthetic_data(rgr_control, iterations, environment, **kwargs)
    charpair_distribution = dict()
    for charpair in environment['simulated_choices']:
        charpair_distribution[charpair] = charpair_distribution.get(charpair, 0) + 1

    if games is None:
        games = get_games_for_players(players)

    real_world_distribution = find_distribution_of_charpairs_from_players_collective_games(players, games)

    # Normalise the values
    number_of_real_world_games = len(games)
    for charpair, count in charpair_distribution.items():
        charpair_distribution[charpair] = (count / iterations) * number_of_real_world_games

    print(sum(environment['confidence'].values()) / len(environment['confidence']))

    # Make ordered distribution lists to account for unordered dicts
    real_ordered_distribution, simulated_ordered_distribution = list(), list()
    chars = list(char_ordering.keys())
    for char1_index in range(len(chars)):
        for char2_index in range(char1_index+1, len(chars)):
            pair = chars[char1_index] + chars[char2_index]
            real_ordered_distribution.append(real_world_distribution.get(pair, 0))
            simulated_ordered_distribution.append(charpair_distribution.get(pair, 0))

    simulated_ordered_distribution = list(map(lambda x: x / 2,
                                              simulated_ordered_distribution))
    print(real_ordered_distribution, simulated_ordered_distribution)
    return (real_ordered_distribution, simulated_ordered_distribution)


def compare_single_player_data(rgr_control, iterations, player="apropos0", games=None, season=1, **kwargs):
    return compare_with_multiple_players(rgr_control, iterations, [player], games, season)

# [None, mitigate, [compare_with_multiple, *args], {mitigation_iterations=, init_seed=, **kwargs}]

def parallelisable_with_seed(argset):
    random_seed, f, args, kwargs = argset[:4]

    # parallelising safely — we pass in an optional dictionary proxy for movefile cache so we don't duplicate file reads
    if len(argset) > 4:
        movefile_cache = argset[4]

    if random_seed is not None:
        seed(random_seed)

    if args != [] and args != ([],):
        return f(*args, **kwargs)
    else:
        return f(**kwargs)

def mitigate_randomness(f, *args, mitigation_iterations=5, init_seed=0, **kwargs):
    results = list()

    parallel_args = [(init_seed + offset, f, args, kwargs, movefile_cache) for offset in range(mitigation_iterations)]
    p = ThreadPoolExecutor(max_workers=1)
    results = list(p.map(parallelisable_with_seed, parallel_args))

    # for seed_offset in range(mitigation_iterations):
    #     seed(init_seed+seed_offset)
    #     results.append(f(*args, **kwargs))

    first = lambda tup: tup[0]
    second = lambda tup: tup[1]
    real_world_data = list(map(first, results))
    simulated_data = list(map(second, results))

    # transform the data into lists of choices for 1st charpair, 2nd charpair, and so on (rather than grouping/ordering by simulation iteration)
    real_choice_counts_by_charpair = zip(*real_world_data)
    simulated_choice_counts_by_charpair = zip(*simulated_data)

    # sum and normalise the data grouped by charpair
    def normalise(l):
        return sum(l)/mitigation_iterations
    real_choice_distribution = list(map(normalise, real_choice_counts_by_charpair))
    simulated_choice_distribution = list(map(normalise, simulated_choice_counts_by_charpair))

    return real_choice_distribution, simulated_choice_distribution

# def k_fold_by_players(players, iterations, fold_count=5, correlation_metric=lambda x: kendalltau(x).pvalue, games=None, *args, **kwargs):
#     if games is None:
#         games = get_games_for_players(players)
#
#     # Randomise game order
#     __import__("random").shuffle(games)
#
#     folds = list()  # Format is [(training1, testing1), (training2, testing2)]
#     for fold_index in range(fold_count):
#         start_index = int(fold_index * len(games) / fold_count)
#         end_index = int((1 + fold_index) * len(games) / fold_count)
#
#         #               training                                           testing
#         folds.append( [ games[0:start_index]+games[end_index:len(games)], games[start_index:end_index] ] )
#
#     performances = list()
#     for training, testing in folds:
#         # perform optimisation on the training fold of games for these players
#         # maybe annealing? Maybe a simple grid search?
#         # Here's a simple grid search to get started
#         bestguess = 0
#         depth = 4
#         level = 1
#         for d in range(depth):
#             level *= 0.1
#             newbestguess = None
#             for g in range(1,10):
#                 newguess = bestguess + g*level
#                 if newbestguess is not None:
#                     # Get the correlation of newbestguess (there's an lru cache on the multiple iter method)
#                     corr_newbestguess = correlation_metric(*mitigate_randomness(compare_with_multiple_players, newbestguess, iterations, games=training, players=players, *args, **kwargs))
#                     # Get the correlation of newguess
#                     corr_newguess = correlation_metric(*mitigate_randomness(compare_with_multiple_players, newguess, iterations, games=training, players=players, *args, **kwargs))
#
#                     # set newbestguess to be the better of the two
#                     if corr_newguess < corr_newbestguess:
#                         newbestguess = newguess
#
#             # We've found the best value from all the decimal points between 1 and 9.
#             # Effectively, bestguess is currently the decimal point 0 for the level we're currently at
#             # (it's equivalent to g = 0 in the newguess setter above)
#             # So, we check the best from our search against the best from before, accept the winner.
#             corr_newbestguess = correlation_metric(*mitigate_randomness(compare_with_multiple_players, newbestguess, iterations, games=training, players=players, *args, **kwargs))
#             corr_bestguess = correlation_metric(*mitigate_randomness(compare_with_multiple_players, bestguess, iterations, games=training, players=players, *args, **kwargs))
#
#             if corr_newbestguess < corr_bestguess:
#                 bestguess = newbestguess
#
#         # We now have an rgr value for _one_ training set. How does it perform for the testing set?
#         # Measure how well it correlates to the corresponding test set.
#         # Add this to the performances list in a manner that lets us compare performances and find its respective rgr
#         performances.append([bestguess, correlation_metric(*mitigate_randomness(compare_with_multiple_players, bestguess, iterations, games=testing, players=players, *args, **kwargs))])
#
#
#     # Pick the best of the testing correlations, according to what we got from the above grid search
#     # NOTE: assuming that hasn't been updated/replaced
#     return max(performances, key=lambda p: p[1])
#

def k_fold_by_players(players, iterations, fold_count=5, correlation_metric=lambda x: kendalltau(x).pvalue, games=None, *args, **kwargs):
    if games is None:
        games = get_games_for_players(players)

    # Randomise game order
    __import__("random").shuffle(games)

    folds = list()  # Format is [(training1, testing1), (training2, testing2)]
    for fold_index in range(fold_count):
        start_index = int(fold_index * len(games) / fold_count)
        end_index = int((1 + fold_index) * len(games) / fold_count)

        #               training                                           testing
        folds.append( [ games[0:start_index]+games[end_index:len(games)], games[start_index:end_index] ] )

    performances = list()
    for training, testing in folds:
        # perform optimisation on the training fold of games for these players
        # maybe annealing? Maybe a simple grid search?
        # Here's a simple grid search to get started
        bestguess = 0
        depth = 4
        level = 1
        for d in range(depth):
            level *= 0.1
            possible_rgrs_at_level = [bestguess + g*level for g in range(10)]

            p = ThreadPoolExecutor(max_workers=1)
            kwarg_list = {'games':games, 'players':players, 'iterations':iterations}
            kwarg_list.update(kwargs)

            # A mad construct for Good Reasons. Pytho's multiprocessing Pool objects require a pickle-able function (so defined at module level). We use `parallelisable_with_seed` to unpack args and control randomness.
            # Because of this, we have to provide a list of arguments containing a seed, function to run, and args & kwargs too.
            arglists = [[0, mitigate_randomness, [compare_with_multiple_players, []], dict({'rgr_control':mapped_rgr}, **kwarg_list)] for mapped_rgr in possible_rgrs_at_level]
            results = list(p.map(parallelisable_with_seed, arglists))  # Runs the above functions with this mad notation to make Python parallel processes do its thing easily
            # Get results from our correlation metric
            correlation_results = list(map(lambda result: correlation_metric(*result), results))
            bestguess = min(zip(possible_rgrs_at_level, correlation_results), key=lambda result: result[1])
            bestguess = bestguess[0] # the actual rgr, not the tuple from the zip
            # newbestguess = correlation_metric(*mitigate_randomness(compare_with_multiple_players, bestguess, iterations, games=training, players=players, *args, **kwargs))
            # for g in range(1, 10):
            #     newguess = bestguess + g*level
            #     if newbestguess is not None:
            #         # Get the correlation of newbestguess (there's an lru cache on the multiple iter method)
            #         corr_newbestguess = correlation_metric(*mitigate_randomness(compare_with_multiple_players, newbestguess, iterations, games=training, players=players, *args, **kwargs))
            #         # Get the correlation of newguess
            #         corr_newguess = correlation_metric(*mitigate_randomness(compare_with_multiple_players, newguess, iterations, games=training, players=players, *args, **kwargs))
            #
            #         # set newbestguess to be the better of the two
            #         if corr_newguess < corr_newbestguess:
            #             newbestguess = newguess
            #
            # # We've found the best value from all the decimal points between 1 and 9.
            # # Effectively, bestguess is currently the decimal point 0 for the level we're currently at
            # # (it's equivalent to g = 0 in the newguess setter above)
            # # So, we check the best from our search against the best from before, accept the winner.
            # corr_newbestguess = correlation_metric(*mitigate_randomness(compare_with_multiple_players, newbestguess, iterations, games=training, players=players, *args, **kwargs))
            # corr_bestguess = correlation_metric(*mitigate_randomness(compare_with_multiple_players, bestguess, iterations, games=training, players=players, *args, **kwargs))
            #
            # if corr_newbestguess < corr_bestguess:
            #     bestguess = newbestguess
            #
        # We now have an rgr value for _one_ training set. How does it perform for the testing set?
        # Measure how well it correlates to the corresponding test set.
        # Add this to the performances list in a manner that lets us compare performances and find its respective rgr
        performances.append([bestguess, correlation_metric(*mitigate_randomness(compare_with_multiple_players, bestguess, iterations, games=testing, players=players, *args, **kwargs))])


    # Pick the best of the testing correlations, according to what we got from the above grid search
    # NOTE: assuming that hasn't been updated/replaced
    performance_values = list(map(lambda x: x[1], performances))
    return performances, sum(performance_values)/fold_count


def calculate_entropy_from_real_and_simulated_distributions(real, simulated):
    difference_distribution = dict()
    for index in range(len(real)):
        difference_distribution[index] = abs(real[index]-simulated[index])
    return calculate_entropy(difference_distribution)


def calculate_entropy(distributed_choices):
    def prob(num):
        return num/sum(distributed_choices)
    return -sum(list(map(lambda x: 0 if prob(x) == 0 else prob(x)-log2(prob(x)), distributed_choices)))

def distance_on_probability_dist_sphere(real, simulated):
    snd = lambda x: x[1]
    fst = lambda x: x[0]

    real_sorted = sorted(real.items(), key=fst)
    sim_sorted = sorted(simulated.items(), key=fst)

    real_vector = map(snd, real_sorted)
    sim_vector = map(snd, sim_sorted)

    assert len(real_vector) == len(sim_vector)

    dotprod = sum(real_vector[i]*sim_vector[i] for i in range(len(real_vector)))
    sphere_radius = sqrt(sum(map(lambda x: x**2, real_vector)))

    # geodesic length is effectively r*angle, where angle is 2 * arcsin( length / 2r )
    # https://math.stackexchange.com/questions/225323/length-of-arc-connecting-2-points-in-n-dimensions
    theta = 2*asin(sqrt(dotprod)/(2*sphere_radius))
    distance = sphere_radius * theta

    return distance

def get_games_for_players(players):
    games = list()
    for player in players:
        shepherd.config.game_filters.append(lambda game: player in game.get('usernames', []))
    games = shepherd.filtered_games()
    for _player in players:
        shepherd.config.game_filters.pop()
    return games

if __name__ == "__main__":

    # for concurrency safety
    freeze_support()  # necessary for debugging I think?!?!
    manager = Manager()
    movefile_cache = {}#manager.dict(movefile_cache)
    print("Populating movefile cache")
    chars = ['K', 'A', 'M', 'H', 'R', 'W', 'G', 'B']
    for i in range(8):
        for j in range(i+1, 8):
            try:
                add_to_movefile_cache("../lookupV2/season" + str(season) + "/" + chars[i]+chars[j] + ".txt")
            except:
                add_to_movefile_cache("../lookupV2/season" + str(season) + "/" + chars[j]+chars[i] + ".txt")
    print("Populated movefile cache")

    print(k_fold_by_players(players=['apropos0', 'Frp97', 'Luca1802', 'creilly1'], correlation_metric=calculate_entropy_from_real_and_simulated_distributions, fold_count=3, iterations=10000, print_progress=True))

    # # For plotting confidence
    # def conf_finder(env):
    #     player = 0
    #     return games_played_by(player, env), env['confidence'][player]
    #
    # results = dict()
    # r = dict()
    # iterations = 1000
    # for rgr in [0.0001, 0.01, 0.1, 0.3, 0.5, 0.8]:
    #     data = mitigate_randomness(compare_single_player_data, rgr, iterations, mitigation_iterations=7)
    #     results[rgr] = data
    #     r[rgr] = kendalltau(*data)
    #     print(r[rgr])
    # print(r)
    # plt.plot(list(zip(list(r.keys()), list(map(lambda v: v.pvalue, r.values())))))
    # plt.show()


