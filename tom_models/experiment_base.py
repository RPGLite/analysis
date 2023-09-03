from statistics import correlation
from typing import Optional
from shepherd import Shepherd, ShepherdConfig
from pdsf import *
from helper_fns import *
from random import seed
from datetime import datetime
from scipy.stats import kendalltau
from scipy.optimize import dual_annealing
from aspects import *
from game_processing import convert_gamedoc_to_tom_compatible, flip_state, process_lookup2, get_games_for_players, find_distribution_of_charpairs_from_players_collective_games, find_distribution_of_charpairs_for_user_from_gameset
from dataclasses import dataclass
from functools import partial
import gc
import birch_curve_calculation_utilities as curveutils

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


@dataclass
class ModelParameters:
    c: float
    curve_inflection_relative_to_numgames: float
    prob_bored: float
    boredom_enabled: bool
    training_data: list
    testing_data: list
    assumed_confidence_plateau: float
    starting_confidence: float
    iteration_base: int
    number_simulated_players: int
    advice: list[tuple[str, str, str|callable]]
    players:list[str]
    args:list[any]
    kwargs:dict[str:any]
        
    def __repr__(self) -> str:
        return f"params for {', '.join(self.players)}:c={self.c}, prob bored={self.prob_bored}, boredom {'en' if self.boredom_enabled else 'dis'}abled, confidence model assumes low of {self.starting_confidence}, high of {self.assumed_confidence_plateau}, iteration base={self.iteration_base}, #simulated players={self.number_simulated_players}, rgr inflection relative to #games={self.curve_inflection_relative_to_numgames}, #training games={len(self.training_data)}, #testing games={len(self.testing_data)}"

    def __getstate__(self) -> object:
        state = self.__dict__.copy()
        pickleable_advice = list()
        for type, join_point, aspect in state['advice']:
            pickleable_advice.append((type, join_point, aspect.__name__))
        state['advice'] = pickleable_advice
        return state

    def __setstate__(self, d):
        self.__dict__ = d
        unpickled_advice = list()
        for type, join_point, aspect in d['advice']:
            unpickled_advice.append((type, join_point, eval(aspect)))
        self.advice = unpickled_advice
        if 'args' not in d:
            self.args = list()
        if 'kwargs' not in d:
            self.kwargs = dict()

    @property
    def boredom_period(self) -> int:
        '''
        Number of games to play before checking player boredom.
        Attempts to allow every player combo to play each other once on average before checking again.
        '''
        return int(self.number_simulated_players**2)/2

    def active_dataset(self, testing) -> list:
        return self.testing_data if testing else self.training_data

    def iterations(self, testing) -> int:
        if self.boredom_enabled:
            return self.iteration_base
        
        return int(self.number_simulated_players**2 * len(self.active_dataset(testing)) / 2)

    def rgr(self, testing) -> float:
        '''
        RGR for this C value, number of games to play, and start/end confidences.
        '''
        if not hasattr(self, '_rgr_cache'):
            self._rgr_cache = dict()
        if self._rgr_cache.get(testing) is None:
            num_games_to_confidence = len(self.active_dataset(testing)) * self.curve_inflection_relative_to_numgames
            self._rgr_cache[testing] = curveutils.rgr_yielding_num_games_for_c(num_games_to_confidence,
                                                                        self.c,
                                                                        start=self.starting_confidence,
                                                                        limit=self.assumed_confidence_plateau)
        return self._rgr_cache[testing]
        
    def run_experiment(self, testing, correlation_metric):
        real, synthetic = compare_with_multiple_players(rgr_control=self.rgr(testing=False),
                                                                    iterations=self.iterations(testing=False),
                                                                    games=self.training_data,
                                                                    players=self.players,
                                                                    birch_c=self.c,
                                                                    sigmoid_initial_confidence=self.starting_confidence,
                                                                    boredom_confidence=self.assumed_confidence_plateau,
                                                                    num_synthetic_players=self.number_simulated_players,
                                                                    boredom_period=self.boredom_period,
                                                                    prob_bored=self.prob_bored,
                                                                    advice=self.advice,
                                                                    *self.args,
                                                                    **self.kwargs)
        return Result(self, real, synthetic, correlation_metric, testing)
        
        


@dataclass
class Result:
    params:ModelParameters
    real_distribution:list[float]
    simulated_distribution:list[float]
    correlation_metric:Optional[callable]
    testing: bool

    def __getstate__(self) -> object:
        return {k: v for k, v in self.__dict__.items() if not callable(v)}

    def __setstate__(self, d) -> object:
        self.__dict__ = d
        if 'correlation_metric' not in d or not callable(d['correlation_metric']):
            self.correlation_metric = kendalltau

    @property
    def pval(self) -> float:
        return self.correlation_metric(self.real_distribution, self.simulated_distribution).pvalue

    @property
    def statistic(self) -> float:
        return self.correlation_metric(self.real_distribution, self.simulated_distribution).statistic

    def within_acceptable_bounds(self, pval_threshold:float, statistic_threshold:float) -> bool:
        return self.pval < pval_threshold and self.statistic > statistic_threshold

    def __repr__(self) -> str:
        return f"{', '.join(self.params.players)} with c={self.params.c}, rgr={self.params.rgr(self.testing)}, prob_bored={self.params.prob_bored if self.params.boredom_enabled else 'DISABLED'}\tyielded pval={self.pval}, statistic={self.statistic}"

def normalise_distrubutions_from_datsets(results:list,
                                         randomness_mitigation_iterations: int):

        first = lambda tup: tup[0]
        second = lambda tup: tup[1]
        real_world_data = list(map(first, results))
        simulated_data = list(map(second, results))

        # transform the data into lists of choices for 1st charpair, 2nd charpair, and so on (rather than grouping/ordering by simulation iteration)
        real_choice_counts_by_charpair = zip(*real_world_data)
        simulated_choice_counts_by_charpair = zip(*simulated_data)

        # sum and normalise the data grouped by charpair
        def normalise(l):
            return sum(l)/randomness_mitigation_iterations

        real_choice_distribution = list(map(normalise, 
                                            real_choice_counts_by_charpair))
        simulated_choice_distribution = list(map(normalise,
                                                simulated_choice_counts_by_charpair))

        return real_choice_distribution, simulated_choice_distribution

def fit_curve_param(folds,
                    correlation_metric,
                    depth:int,
                    iterations:int, # Number of games to simulate when generating data
                    games,
                    players:list[str],
                    advice:list[tuple[str, str, str]],
                    cvals_to_explore:list[float]=[0.1, 0.2, 0.5, 1, 2, 5, 10],
                    inflection_point_positions:list[float]=[0.25, 0.5, 1, 2], # Proportion of games used to calculate rgr
                    correlation_threshold=0.20,
                    correlation_limit_good=0.4,
                    pval_threshold=0.05,
                    pval_threshold_good=0.02,
                    starting_confidence=0.1,
                    assumed_confidence_plateau=0.9,
                    random_seed:int=0,
                    randomness_mitigation_iterations=1, # runs model multiple times and normalises results. Maybe I should always leave this as 1?
                    num_simulated_players=15,
                    prob_bored_to_explore=[0.25, 0.75, 1],
                    test_with_no_boredom=True,
                    print_debuglines=False,
                    *args,
                    **kwargs):
    model_parameters_by_fold:list[list[ModelParameters]] = []

    for training, testing in folds:
        model_parameters = list()
        for c in cvals_to_explore:
            for curve_inflection_position_relative_to_numgames in inflection_point_positions:
                for prob_bored in prob_bored_to_explore:
                    model_parameters.append(ModelParameters(c=c,
                                                            curve_inflection_relative_to_numgames=curve_inflection_position_relative_to_numgames,
                                                            prob_bored=prob_bored,
                                                            boredom_enabled=True,
                                                            training_data=training,
                                                            testing_data=testing,
                                                            assumed_confidence_plateau=assumed_confidence_plateau,
                                                            starting_confidence=starting_confidence,
                                                            iteration_base=iterations,
                                                            number_simulated_players=num_simulated_players,
                                                            advice=advice,
                                                            players=players,
                                                            args=args,
                                                            kwargs=kwargs))
                if test_with_no_boredom:
                    model_parameters.append(ModelParameters(c=c,
                                                            curve_inflection_relative_to_numgames=curve_inflection_position_relative_to_numgames,
                                                            prob_bored=0.0001,
                                                            boredom_enabled=False,
                                                            training_data=training,
                                                            testing_data=testing,
                                                            assumed_confidence_plateau=1-starting_confidence, # ideally it'd be 1, but then we can't calculate the RGR.
                                                            starting_confidence=starting_confidence,
                                                            iteration_base=iterations,
                                                            number_simulated_players=num_simulated_players,
                                                            advice=advice,
                                                            players=players,
                                                            args=args,
                                                            kwargs=kwargs))
        model_parameters_by_fold.append(model_parameters)

    fold_results = [] # Result for each testing fold in folds.
    foldnum = 0
    lasttime = datetime.now()
    for model_parameters in model_parameters_by_fold:
        foldnum += 1
        param_results:list[Result] = []
        for params in model_parameters:

            training, testing = params.training_data, params.testing_data

            seed(random_seed)
            random_seed += 1

            results = []
            for _ in range(randomness_mitigation_iterations):
                results.append(compare_with_multiple_players(rgr_control=params.rgr(testing=False),
                                                             iterations=params.iterations(testing=False),
                                                             games=params.training_data,
                                                             players=params.players,
                                                             birch_c=params.c,
                                                             sigmoid_initial_confidence=params.starting_confidence,
                                                             boredom_confidence=params.assumed_confidence_plateau,
                                                             num_synthetic_players=params.number_simulated_players,
                                                             boredom_period=params.boredom_period,
                                                             prob_bored=params.prob_bored,
                                                             advice=params.advice,
                                                             *args,
                                                             **kwargs))
            
            # We need to average the distributions from the set of results we generated
            # (one set of results for every randomness mitigation iteration)
            real_distribution, simulated_distribution = normalise_distrubutions_from_datsets(results,
                                                                                             randomness_mitigation_iterations)
            
            param_results.append(Result(params=params,
                                        real_distribution=real_distribution,
                                        simulated_distribution=simulated_distribution,
                                        correlation_metric=correlation_metric,
                                        testing=False))

            if print_debuglines:
                currtime = datetime.now()
                print(f"DEBUG took {(currtime-lasttime).total_seconds()}s  ::\t{param_results[-1]}")
                lasttime = currtime

        # Now we've iterated through all of the parameters we wanted to anneal on for this fold.
        # Which was "best"?

        # Filter for "good" correlation and choose the best p-val which meets that threshold
        # If no good correlations exist, filter for low correlation and choose the best p-val which meets that threshold
        # If we don't even have low correlation, pick the best p-val for a positive correlation
        # If that doesn't exist, pick the highest correlation.

        # good_correlation = partial(filter, lambda result: result.statistic > correlation_limit_good)
        # low_correlation = partial(filter, lambda result: result.statistic > correlation_threshold)
        # any_correlation = partial(filter, lambda result: result.statistic > 0)

        # good_pval = partial(filter, lambda result: result.pval < 0.01)
        # low_pval = partial(filter, lambda result: result.pval < 0.02)
        # usable_pval = partial(filter, lambda result: result.pval < 0.05)

        # ideal_result = None # Will eventually become the result that meets our correlation and pvalue thresholds.
        # for result_filter in [good_correlation,
        #                       low_correlation,
        #                       any_correlation]:
        #     results_matching_correlation_filter = list(result_filter(param_results))
        #     results_matching_pval_filter = list()

        #     if len(results_matching_correlation_filter) == 0:
        #         continue # We need a less strict filter, so don't select anything from this one.

        #     # We've got at least one result matching our filter, so further filter by pval
        #     for pval_filter in [good_pval,
        #                         low_pval,
        #                         usable_pval]:
        #         results_matching_pval_filter = list(pval_filter(results_matching_correlation_filter))

        #         if len(results_matching_pval_filter) == 0:
        #             continue
                
        #         ideal_result = max(results_matching_pval_filter, key=lambda result: result.statistic)  # A high correlation we're certain of to some degree
        #         break

        #     if ideal_result is not None:
        #         break

        # if ideal_result is None:
        #     ideal_result = max(param_results, key=lambda result: result.statistic)

        usable_results = [res for res in param_results if res.within_acceptable_bounds(pval_threshold, correlation_threshold)]


        # Now, run with testing fold to generate final results.
        test_results = list()
        for res in usable_results:
            print(f"When training fold {foldnum} for {', '.join(players)}, found c={res.params.c}\trgr={res.params.rgr(testing=False)}\tpval={res.pval}\tstatistic={res.statistic}")

            param = res.params
            param_testing_results = list()
            for _ in range(randomness_mitigation_iterations):
                    param_testing_results.append(compare_with_multiple_players(rgr_control=param.rgr(testing=True),
                                                                iterations=param.iterations(testing=True),
                                                                games=param.training_data,
                                                                players=param.players,
                                                                birch_c=param.c,
                                                                sigmoid_initial_confidence=param.starting_confidence,
                                                                boredom_confidence=param.assumed_confidence_plateau,
                                                                num_synthetic_players=param.number_simulated_players,
                                                                boredom_period=param.boredom_period,
                                                                prob_bored=param.prob_bored,
                                                                advice=param.advice,
                                                                *args,
                                                                **kwargs))

            # We need to average the distributions from the set of results we generated
            # (one set of results for every randomness mitigation iteration)
            real_distribution, simulated_distribution = normalise_distrubutions_from_datsets(param_testing_results,
                                                                                            randomness_mitigation_iterations)
            test_res = Result(params=param,
                              real_distribution=real_distribution,
                              simulated_distribution=simulated_distribution,
                              correlation_metric=correlation_metric,
                              testing=True)

            print(f"When testing for {foldnum} for {', '.join(players)}, found c={test_res.params.c}\trgr={test_res.params.rgr(testing=True)}\tprob_bored={test_res.params.prob_bored}\tpval={test_res.pval}\tstatistic={test_res.statistic}")
            if test_res.within_acceptable_bounds(pval_threshold, correlation_threshold):
                test_results.append(test_res)
            else:
                print("Discarding param; didn't meet thresholds for significance under test.")

        fold_results.append(test_results)

        print(f"Finished fold {foldnum} for {', '.join(players)} at {datetime.now().time().isoformat(timespec='auto')}.")
        print()
    
    print("\n")
    print(f"Conclusion for {', '.join(players)}:")
    for res_list in fold_results:
        for res in res_list:
            print(f"\tpval {res.pval}\tstatistic {res.statistic}\trgr {res.params.rgr(testing=True)}\tc {res.params.c}")

    return fold_results
        


def generate_synthetic_data(rgr_control,
                            environment,
                            params:ModelParameters,
                            print_progress=False,
                            initial_exploration=28,
                            boredom_period=25,
                            *args,
                            **kwargs):  # boredom period is probably usefully set as (num players / 2) squared. Means the players have the opportunity to play each other, but we're not waiting forever; it's the area of a half of an adjacency matrix, roughly.

    advice = params.advice
    iterations = params.iterations
    num_synthetic_players = params.number_simulated_players
    sigmoid_initial_confidence = params.starting_confidence
    boredom_confidence = params.assumed_confidence_plateau
    prob_bored = params.prob_bored
    birch_c = params.c

    # Some setup for properly passing values around.
    environment['special vals'] = dict()
    environment['special vals']['rgr'] = rgr_control
    environment['special vals']['sigmoid type'] = "birch controlled"
    environment['special vals']['birch c'] = birch_c
    environment['special vals']['sigmoid initial confidence'] = sigmoid_initial_confidence
    environment['special vals']['initial_exploration'] = initial_exploration

    rule_removers = list()
    aspect_application_methods = {
        'prelude': AspectHooks.add_prelude,
        'around': AspectHooks.add_around,
        'encore': AspectHooks.add_encore,
        'within': AspectHooks.add_fuzzer,
        'error_handler': AspectHooks.add_error_handler,
    }
    for aspect_type, join_point, aspect in advice:
        rule_removers.append(aspect_application_methods[aspect_type](join_point, aspect))

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
        play_game(matchup, environment)

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
        print(performances)

        # Pick the best of the testing correlations, according to what we got from the above grid search
        # NOTE: assuming that hasn't been updated/replaced
        # performance_values = list(map(lambda x: x[1], performances))
        return list(zip(performances, folds))
    elif optimisation == "anneal_c_rgr":
        performances = fit_curve_param(folds, correlation_metric, depth, iterations, games, players, *args, **kwargs)
        print(performances)
        return performances
    else:
        print(f"Unrecognised optimisation algorithm {optimisation}; aborting.")
        exit()

    # perform optimisation on the training fold of games for these players


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

