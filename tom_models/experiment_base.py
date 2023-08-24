from statistics import correlation
from shepherd import Shepherd, ShepherdConfig
from pdsf import *
from helper_fns import *
from random import seed
from datetime import datetime
from scipy.stats import kendalltau
from scipy.optimize import dual_annealing
from aspects import handle_player_cannot_win, record_player_sees_winning_team, around_choosing_chars_based_on_sigmoid, record_simulated_choices, best_move_generator, update_confidence_model
from aspects import hyperbolic_character_choice_from_win_record, track_game_outcomes, around_choosing_chars_based_on_prior_distribution
from aspects import char_ordering  # separate from the above a) the above is mammoth and b) it should find a new home
from game_processing import convert_gamedoc_to_tom_compatible, flip_state, process_lookup2, get_games_for_players, find_distribution_of_charpairs_from_players_collective_games, find_distribution_of_charpairs_for_user_from_gameset
import gc
from datetime import datetime

from tom_models.experiment_base_fitting_curve_param import fit_curve_param

with AspectHooks():
    from base_model import *

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
                            advice : list[tuple[str, str, str]] = list() , # A list of tuples of string join points, aspects to apply, and types of aspect to weave.
                            games=list(),
                            players=list(),
                            garbage_collect_intermittently=False,
                            num_synthetic_players=15,
                            sigmoid_initial_confidence=0.1,
                            initial_exploration=56,
                            boredom_confidence=0.9, # 1 to disable boredom and keep players indefinitely
                            prob_bored=0.25, # 1 to ensure that players are removed when the boredom confidence level is met
                            sigmoid_used="birch controlled",  # "logistic" for logistic curve, "birch" for birch curve.
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
    if len(advice) == 0:
        # manual configuration
        rule_removers.append(AspectHooks.add_prelude('choose*', update_confidence_model))
        rule_removers.append(AspectHooks.add_around('choose*', hyperbolic_character_choice_from_win_record))
        # rule_removers.append(AspectHooks.add_around('generate*', around_simulation_records_prior))
        # rule_removers.append(AspectHooks.add_around('choose*', around_choosing_chars_based_on_prior_distribution))
        # rule_removers.append(AspectHooks.add_around('choose*', around_choosing_chars_based_on_sigmoid))
        rule_removers.append(AspectHooks.add_encore('play_game', record_simulated_choices))
        rule_removers.append(AspectHooks.add_encore('play_game', track_game_outcomes))
        rule_removers.append(AspectHooks.add_encore('play_game', record_player_sees_winning_team))
        rule_removers.append(AspectHooks.add_encore('get_moves_from_table', best_move_generator()))
        rule_removers.append(AspectHooks.add_error_handler('take_turn', handle_player_cannot_win))
    else:
        aspect_application_methods = {
            'prelude': AspectHooks.add_prelude,
            'around': AspectHooks.add_around,
            'encore': AspectHooks.add_encore,
            'within': AspectHooks.add_fuzzer,
            'error_handler': AspectHooks.add_error_handler,
        }
        for aspect_type, join_point, aspect in advice:
            rule_removers.append(aspect_application_methods[aspect_type](join_point, aspect))
        # rule_removers = [aspect_application_methods[aspect_type](join_point, aspect) for aspect_type, join_point, aspect in advice]

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

            if print_progress:
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


def mitigate_randomness(f, *args, mitigation_iterations=10, init_seed=0, **kwargs):
    results = list()

    # We make a set of arguments which includes a bunch of different random seeds for `parallelisable_with_seed` to set.
    # Now we will have run the same function many times, and we can take the
    parallel_args = [(init_seed + offset, f, args, kwargs, movefile_cache) for offset in range(mitigation_iterations)]
    # executor = ThreadPoolExecutor(max_workers=mitigation_iterations) # Execute each iteration in parallel
    # results = list(executor.map(parallelisable_with_seed, parallel_args))
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
    real_choice_distribution = list(map(normalise, 
                                        real_choice_counts_by_charpair))
    simulated_choice_distribution = list(map(normalise,
                                             simulated_choice_counts_by_charpair))

    return real_choice_distribution, simulated_choice_distribution

# Correlation threshold is the minimum correlation value we'll accept before selecting RGRs based on pval
def grid_search(folds, correlation_metric, depth, iterations, games, players, correlation_threshold=0.15, *args, **kwargs):
    performances = list()
    
    # executor = ThreadPoolExecutor(max_workers=10) # one worker per RGR tested at the level we're searching (10 numbers for base 10)

    fold_count = 0
    for training, testing in folds:

        fold_count += 1
        print(f"Starting fold {fold_count}. Time is {datetime.now().isoformat()}\n\n\n")

        bestguess = 0
        level = 1
        meeting_threshold = True # Indicates whether we found _any_ correlation statistics above threshold for rgr in past run
        previously_met_threshold = True # Used to see whether we're repeatedly failing, and break early if so (to avoid thrashing uselessly)
        for d in range(depth):
            if meeting_threshold or bestguess == 0: # If we're meeting correlation threshold, or just beginning to search
                search_pivots = [bestguess]
            else:
                search_pivots = [0.1, 0.3, 0.5, 0.7, 0.9]
            
            # Move level forward (didn't earlier so that we could use level in search pivots)
            level *= 0.1

            possible_rgrs_at_level = [pivot + g * level for g in range(1, 10) for pivot in search_pivots]
            # We need to check above _and_ below the previous best guess we picked, but we only want to do this on the
            # second iteration onward so that we don't test negative rgrs.
            if level < 0.1:
                possible_rgrs_at_level += [pivot - g * level for g in range(10) for pivot in search_pivots]

            # If we're not meeting correlation threshold, the above will miss out RGRs 0.2, 0.4, 0.6, and 0.8. Add those now.

            possible_rgrs_at_level += [pivot * level for pivot in [0.2, 0.4, 0.6, 0.8]]

            kwarg_list = {'games': training, 'players': players, 'iterations': iterations}
            kwarg_list.update(kwargs)

            # A mad construct for Good Reasons. Python's multiprocessing Pool objects require a pickle-able function (so defined at module level). We use `parallelisable_with_seed` to unpack args and control randomness.
            # Because of this, we have to provide a list of arguments containing a seed, function to run, and args & kwargs too.
            arglists = [
                [0, mitigate_randomness, [compare_with_multiple_players, []], dict({'rgr_control': mapped_rgr}, **kwarg_list),
                 movefile_cache] for mapped_rgr in possible_rgrs_at_level]
            # results = list(executor.map(parallelisable_with_seed, arglists))
            results = list(map(parallelisable_with_seed, arglists))

            # Get results from our correlation metric
            correlation_certainties = list(map(lambda result: correlation_metric(*result).pvalue, results))
            correlation_magnitudes = list(map(lambda result: correlation_metric(*result).statistic, results))

            # Find all datapoints where the correlation statistic / magnitude is above the parameterised threshold.
            # If none exist, select only the datapoint with the highest correlation statistic.
            acceptable_correlations_to_select = list()
            for index in range(len(possible_rgrs_at_level)):
               if correlation_magnitudes[index] > correlation_threshold:
                    acceptable_correlations_to_select.append((possible_rgrs_at_level[index], correlation_certainties[index]))

            previously_met_threshold = meeting_threshold
            meeting_threshold = len(acceptable_correlations_to_select) != 0

            # If this is our first run, the only thing we care about is correlation. 
            # After that, we'll begin picking based on pvalue instead.
            # For that reason, we pick the best correlation if none met threshold, OR if level == 0.1
            if len(acceptable_correlations_to_select) == 0 or level == 0.1:
                best_correlation_index = correlation_magnitudes.index(max(correlation_magnitudes))
                acceptable_correlations_to_select = [(possible_rgrs_at_level[best_correlation_index], correlation_certainties[index])]

            bestguess = min(acceptable_correlations_to_select, key=lambda result: result[1])
            bestguess = bestguess[0]  # the actual rgr, not the tuple from the zip

            result_index = possible_rgrs_at_level.index(bestguess)  # they maintain an ordering, so rgr number `i`'s results are also in position `i`
            real, sim = results[result_index]
            
            #print(f"\nsearch for level {level} complete, best rgr guess {bestguess}, pval {correlation_certainties[result_index]} \t statistic {correlation_magnitudes[result_index]}\n\n\n")

            # If we failed to meet threshold TWICE, we're spending loads of time searching, and this is a lost cause.
            if not previously_met_threshold and not meeting_threshold:
                print("EXPERIMENT FAIL, aborting to save time. Thrashing around RGRs but nothing correlates.")
                break

        # We now have an rgr value for _one_ training set. How does it perform for the testing set?
        # Measure how well it correlates to the corresponding test set.
        # Add this to the performances list in a manner that lets us compare performances and find its respective rgr
        test_real, test_sim = mitigate_randomness(compare_with_multiple_players, bestguess, iterations, players, games=testing, *args,
                                                  **kwargs)
        performances.append([bestguess,
                             correlation_metric(test_real, test_sim).pvalue,
                             correlation_metric(test_real, test_sim).statistic,
                             'early_exit' if not previously_met_threshold and not meeting_threshold else 'complete_iteration',
                             test_real, test_sim,
                             real, sim])
        print(list(map(lambda perf: perf[:4], performances)))
        print(f"\n\n\nfinished fold {fold_count}\n\n\n")

    return performances


def k_fold_by_players(players, iterations, fold_count=5, correlation_metric=lambda real, sim: kendalltau(real, sim), games=None, optimisation="old_grid", depth=4, *args, **kwargs):
    if games is None:
        global shepherd
        games = get_games_for_players(players, shepherd)
        #del shepherd

    # Randomise game order
    __import__("random").shuffle(games)

    folds = list()  # Format is [(training1, testing1), (training2, testing2)]
    for fold_index in range(fold_count):
        start_index = int(fold_index * len(games) / fold_count)
        end_index = int((1 + fold_index) * len(games) / fold_count)

        #               training                                           testing
        folds.append( [ games[0:start_index]+games[end_index:len(games)], games[start_index:end_index] ] )

    performances = list()
    if optimisation=="old_grid":
        performances = grid_search(folds, correlation_metric, depth, iterations, games, players, *args, **kwargs)
    elif optimisation == "anneal_c_rgr":
        performances = fit_curve_param(folds, correlation_metric, depth, iterations, games, players, *args, **kwargs)

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

