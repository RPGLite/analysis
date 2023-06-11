from shepherd import Shepherd, ShepherdConfig
from tom_models.pdsf import *
from helper_fns import *
from random import seed
from datetime import datetime
from scipy.stats import kendalltau
from scipy.optimize import dual_annealing
from tom_models.aspects import handle_player_cannot_win, record_player_sees_winning_team, around_choosing_chars_based_on_sigmoid, record_simulated_choices, best_move_generator, update_confidence_model
from tom_models.aspects import hyperbolic_character_choice_from_win_record, track_game_outcomes, around_choosing_chars_based_on_prior_distribution
from tom_models.aspects import char_ordering  # separate from the above a) the above is mammoth and b) it should find a new home
from tom_models.game_processing import convert_gamedoc_to_tom_compatible, flip_state, process_lookup2, get_games_for_players, find_distribution_of_charpairs_from_players_collective_games, find_distribution_of_charpairs_for_user_from_gameset
import gc

with AspectHooks():
    from tom_models.base_model import *

def change_season(newseason):
    global season, shepherd, config
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


config = None  # To be set up for the first time by change_season
shepherd = None  # To be set up for the first time by change_season

# Set the initial season (this makes sure we have an up-to-date DB and all that jazz.)
season = 1
change_season(season)


def generate_synthetic_data(rgr_control,
                            iterations,
                            environment,
                            print_progress=False,
                            aspects=list(),
                            games=list(),
                            players=list(),
                            garbage_collect_intermittently=False,
                            num_synthetic_players=10,
                            sigmoid_initial_confidence=0.1,
                            initial_exploration=28,
                            boredom_confidence=0.98,
                            prob_bored=0.25,
                            sigmoid_used="logistic",  # "logistic" for logistic curve, "birch" for birch curve.
                            boredom_period=25,
                            birch_c=1):  # boredom period is probably usefully set as (num players / 2) squared. Means the players have the opportunity to play each other, but we're not waiting forever; it's the area of a half of an adjacency matrix, roughly.

    # Some setup for properly passing values around.
    environment['special vals'] = dict()
    environment['special vals']['rgr'] = rgr_control
    environment['special vals']['sigmoid type'] = sigmoid_used
    environment['special vals']['birch c'] = birch_c
    environment['special vals']['sigmoid initial confidence'] = sigmoid_initial_confidence
    environment['special vals']['initial_exploration'] = initial_exploration


    rule_removers = list()
    rule_removers.append(AspectHooks.add_prelude('choose*', update_confidence_model))
    rule_removers.append(AspectHooks.add_around('choose*', hyperbolic_character_choice_from_win_record))
    # rule_removers.append(AspectHooks.add_around('generate*', around_simulation_records_prior))
    # rule_removers.append(AspectHooks.add_around('choose*', around_choosing_chars_based_on_prior_distribution))
    # rule_removers.append(AspectHooks.add_around('choose*', around_choosing_chars_based_on_sigmoid))
    rule_removers.append(AspectHooks.add_encore('play_game', record_simulated_choices))
    rule_removers.append(AspectHooks.add_encore('play_game', track_game_outcomes))
    rule_removers.append(AspectHooks.add_encore('play_game', record_player_sees_winning_team))
    rule_removers.append(AspectHooks.add_encore('get_moves_from_table', best_move_generator(environment)))
    rule_removers.append(AspectHooks.add_error_handler('take_turn', handle_player_cannot_win))

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

    old_time = datetime.now()
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

            print("%f seconds per game run" % ( (datetime.now()-old_time).total_seconds()/boredom_period) )
            old_time = datetime.now()

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
                print("%f (%d), rgr %f" % (game_number, iterations, rgr_control))

    for rule_remover in rule_removers:
        AspectHooks.remove(rule_remover)


def compare_with_multiple_players(rgr_control, iterations, players, games=None, new_season=1, **kwargs):
    if season != new_season:
        change_season(new_season)

    environment = dict()

    generate_synthetic_data(rgr_control, iterations, environment, games=games, players=players, **kwargs)
    charpair_distribution = dict()
    for charpair in environment['simulated_choices']:
        charpair_distribution[charpair] = charpair_distribution.get(charpair, 0) + 1

    if games is None:
        games = get_games_for_players(players, shepherd)

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

    # We make a set of arguments which includes a bunch of different random seeds for `parallelisable_with_seed` to set.
    # Now we will have run the same function many times, and we can take the
    parallel_args = [(init_seed + offset, f, args, kwargs, movefile_cache) for offset in range(mitigation_iterations)]
    results = list(map(parallelisable_with_seed, parallel_args))

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

def grid_search(folds, correlation_metric, depth, iterations, games, players, *args, **kwargs):
    performances = list()

    for training, testing in folds:

        bestguess = 0
        level = 1
        for d in range(depth):
            level *= 0.1
            possible_rgrs_at_level = [bestguess + g * level for g in range(1, 10)]
            # We need to check above _and_ below the previous best guess we picked, but we only want to do this on the
            # second iteration onward so that we don't test negative rgrs.
            if level < 0.1:
                possible_rgrs_at_level += [bestguess - g * level for g in range(10)]

            kwarg_list = {'games': training, 'players': players, 'iterations': iterations}
            kwarg_list.update(kwargs)

            # A mad construct for Good Reasons. Python's multiprocessing Pool objects require a pickle-able function (so defined at module level). We use `parallelisable_with_seed` to unpack args and control randomness.
            # Because of this, we have to provide a list of arguments containing a seed, function to run, and args & kwargs too.
            arglists = [
                [0, mitigate_randomness, [compare_with_multiple_players, []], dict({'rgr_control': mapped_rgr}, **kwarg_list),
                 movefile_cache] for mapped_rgr in possible_rgrs_at_level]
            results = list(map(parallelisable_with_seed, arglists))

            # Get results from our correlation metric
            correlation_results = list(map(lambda result: correlation_metric(*result), results))
            bestguess = min(zip(possible_rgrs_at_level, correlation_results), key=lambda result: result[1])
            bestguess = bestguess[0]  # the actual rgr, not the tuple from the zip
            result_index = possible_rgrs_at_level.index(bestguess)  # they maintain an ordering, so rgr number `i`'s results are also in position `i`
            real, sim = results[result_index]

        # We now have an rgr value for _one_ training set. How does it perform for the testing set?
        # Measure how well it correlates to the corresponding test set.
        # Add this to the performances list in a manner that lets us compare performances and find its respective rgr
        test_real, test_sim = mitigate_randomness(compare_with_multiple_players, bestguess, iterations, players, games=testing, *args,
                                                  **kwargs)
        performances.append([bestguess,
                             correlation_metric(test_real, test_sim),
                             test_real, test_sim,
                             real, sim])
        print(performances)

    return performances


def k_fold_by_players(players, iterations, fold_count=5, correlation_metric=lambda real, sim: kendalltau(real, sim).pvalue, games=None, optimisation="grid", depth=4, *args, **kwargs):
    if games is None:
        global shepherd
        games = get_games_for_players(players, shepherd)
        del shepherd

    # Randomise game order
    __import__("random").shuffle(games)

    folds = list()  # Format is [(training1, testing1), (training2, testing2)]
    for fold_index in range(fold_count):
        start_index = int(fold_index * len(games) / fold_count)
        end_index = int((1 + fold_index) * len(games) / fold_count)

        #               training                                           testing
        folds.append( [ games[0:start_index]+games[end_index:len(games)], games[start_index:end_index] ] )

    performances = list()
    if optimisation=="grid":
        performances = grid_search(folds, correlation_metric, depth, iterations, games, players, *args, **kwargs)
    elif optimisation == "simulated annealing":
        for training, testing in folds:
            #TODO: put an annealing implementation here
            pass

    # perform optimisation on the training fold of games for these players

    print(performances)

    # Pick the best of the testing correlations, according to what we got from the above grid search
    # NOTE: assuming that hasn't been updated/replaced
    # performance_values = list(map(lambda x: x[1], performances))
    return list(zip(performances, folds))


if __name__ == "__main__":

    print("Populating movefile cache")
    chars = ['K', 'A', 'M', 'H', 'R', 'W', 'G', 'B']
    for i in range(8):
        for j in range(i+1, 8):
            try:
                add_to_movefile_cache("../lookupV2/season" + str(season) + "/" + chars[i]+chars[j] + ".txt")
            except:
                add_to_movefile_cache("../lookupV2/season" + str(season) + "/" + chars[j]+chars[i] + ".txt")
    print("Populated movefile cache")

    group_games = get_games_for_players(['Frp97'], shepherd)
    print(k_fold_by_players(players=['Frp97'],
                            correlation_metric=kendalltau,
                            fold_count=5,
                            iterations=5000,
                            games=group_games,
                            print_progress=True))

