import random
import birch_curve_calulation_utilities as curveutils
from dataclasses import dataclass
from tom_models.experiment_base import compare_with_multiple_players
from scipy.stats import SignificanceResult
from functools import partial


@dataclass
class ModelParameters:
    c:float
    rgr:float


@dataclass
class Result:
    params:ModelParameters
    real_distribution:list[float]
    simulated_distribution:list[float]
    correlation_metric:callable[[list[float],list[float]], SignificanceResult]

    @property
    def pval(self):
        return self.correlation_metric(self.real_distribution, self.simulated_distribution).pvalue

    @property
    def statistic(self):
        return self.correlation_metric(self.real_distribution, self.simulated_distribution).statistic

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
                    cvals_to_explore:list[float]=[0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 50],
                    inflection_point_positions:list[float]=[0.25, 0.5, 0.75, 1], # Proportion of games used to calculate rgr
                    correlation_threshold=0.15,
                    correlation_limit_good=0.4,
                    starting_confidence=0.1,
                    assumed_confidence_plateau=0.9,
                    random_seed:int=0,
                    randomness_mitigation_iterations=5, # runs model multiple times and normalises results. Maybe I should always leave this as 1?
                    num_simulated_players=15,
                    *args,
                    **kwargs):
    rgr_for_inflection_point_positions = lambda c, position: curveutils.rgr_yielding_num_games_for_c(len(games)*position, c, start=starting_confidence, limit=assumed_confidence_plateau)
    model_parameters:list[ModelParameters] = []
    for c in cvals_to_explore:
        for curve_inflection_position_relative_to_numgames in inflection_point_positions:
            num_games_to_confidence = len(games) * curve_inflection_position_relative_to_numgames
            rgr = curveutils.rgr_yielding_num_games_for_c(num_games_to_confidence,
                                                    c,
                                                    start=starting_confidence,
                                                    limit=assumed_confidence_plateau)
            model_parameters.append(ModelParameters(c=c, rgr=rgr))

    results = [] # Result for each testing fold in folds.
    foldnum = 0
    for training, testing in folds:
        foldnum += 1
        param_results:list[Result] = []
        for params in model_parameters:

            random.seed(random_seed)
            random_seed += 1

            results = []
            for _ in range(randomness_mitigation_iterations):
                results.append(compare_with_multiple_players(rgr_control=params.rgr,
                                                             iterations=iterations,
                                                             games=training,
                                                             players=players,
                                                             birch_c=params.c,
                                                             sigmoid_initial_confidence=starting_confidence,
                                                             boredom_confidence=assumed_confidence_plateau,
                                                             num_synthetic_players=num_simulated_players,
                                                             # How often we check to see if folk are bored. (players^2)/2 gives players the chance to play 1 more game on average again before we check a second time.
                                                             boredom_period=int(num_simulated_players**2)/2,
                                                             sigmoid_used="birch controlled",
                                                             *args,
                                                             **kwargs  # Should include advice to run
                                                             ))
            
            # We need to average the distributions from the set of results we generated
            # (one set of results for every randomness mitigation iteration)
            real_distribution, simulated_distribution = normalise_distrubutions_from_datsets(results,
                                                                                             randomness_mitigation_iterations)
            
            param_results.append(Result(params=params,
                                        real_distribution=real_distribution,
                                        simulated_distribution=simulated_distribution))

        # Now we've iterated through all of the parameters we wanted to anneal on for this fold.
        # Which was "best"?

        # Filter for "good" correlation and choose the best p-val which meets that threshold
        # If no good correlations exist, filter for low correlation and choose the best p-val which meets that threshold
        # If we don't even have low correlation, pick the best p-val for a positive correlation
        # If that doesn't exist, pick the highest correlation.

        good_correlation = partial(filter, lambda result: result.statistic > correlation_limit_good)
        low_correlation = partial(filter, lambda result: result.statistic > correlation_threshold)
        any_correlation = partial(filter, lambda result: result.correlation > 0)

        good_pval = partial(filter, lambda result: result.pvalue < 0.01)
        low_pval = partial(filter, lambda result: result.pvalue < 0.02)
        usable_pval = partial(filter, lambda result: result.pvalue < 0.05)

        ideal_result = None # Will eventually become the result that meets our correlation and pvalue thresholds.
        for result_filter in [good_correlation,
                              low_correlation,
                              any_correlation]:
            results_matching_correlation_filter = list(result_filter(param_results))

            if len(results_matching_correlation_filter) == 0:
                continue # We need a less strict filter, so don't select anything from this one.

            # We've got at least one result matching our filter, so further filter by pval
            for pval_filter in [good_pval,
                                low_pval,
                                usable_pval]:
                results_matching_pval_filter = list(pval_filter(results_matching_correlation_filter))

                if len(results_matching_pval_filter) == 0:
                    continue
                
                ideal_result = max(results_matching_pval_filter, key=lambda result: result.correlation)  # A high correlation we're certain of to some degree
                break

            if ideal_result is not None:
                break

        if ideal_result is None:
            ideal_result = max(results_matching_pval_filter, key=lambda result: result.correlation)

        print(f"When training fold {foldnum} for {', '.join(players)}, found c={ideal_result.c}\trgr={ideal_result.rgr}\tpval={ideal_result.pval}\tstatistic={ideal_result.statistic}")

        # Now, run with testing fold to generate final results.
        for _ in range(randomness_mitigation_iterations):
            results.append(compare_with_multiple_players(rgr_control=params.rgr,
                                                        iterations=iterations,
                                                        games=testing,
                                                        players=players,
                                                        birch_c=params.c,
                                                        sigmoid_initial_confidence=starting_confidence,
                                                        boredom_confidence=assumed_confidence_plateau,
                                                        num_synthetic_players=num_simulated_players,
                                                        # How often we check to see if folk are bored. (players^2)/2 gives players the chance to play 1 more game on average again before we check a second time.
                                                        boredom_period=int(num_simulated_players**2)/2,
                                                        sigmoid_used="birch controlled",
                                                        *args,
                                                        **kwargs  # Should include advice to run
                                                        ))

        # We need to average the distributions from the set of results we generated
        # (one set of results for every randomness mitigation iteration)
        real_distribution, simulated_distribution = normalise_distrubutions_from_datsets(results,
                                                                                        randomness_mitigation_iterations)
        results.append(Result(params=params,
                              real_distribution=real_distribution,
                              simulated_distribution=simulated_distribution))

        print(f"When testing for {foldnum} for {', '.join(players)}, found c={results[-1].c}\trgr={results[-1].rgr}\tpval={results[-1].pval}\tstatistic={results[-1].statistic}")
        print(f"Finished fold {foldnum} for {', '.join(players)}.")
    
    return results
        

        

        

        




            




            
                    
            
                    
