from experiment_base import Result, ModelParameters
from functools import reduce
from copy import copy
from scipy.stats import kendalltau
from multiprocessing import Pool
import pathlib
import argparse
import os
import pickle

def collect_and_analyse(result_dirs, season=1):
    '''
    Takes a list of directories  containing .pickle-format results of experimental runs
    and an optional season (seasons other than `1` not currently supported).
    
    Analyses the resulting information in a manner I'm yet to determine.
    '''
    # walk all dirs to get the files containing results.
    result_files = list()
    for result_dir in result_dirs:
        for (dirpath, dirnames, filenames) in os.walk(result_dir):
            for filename in filenames:
                if filename.endswith('.pickle'): 
                    result_files.append(os.sep.join([dirpath, filename]))
    
    processPool = Pool(10)
    globallyViableParams = processPool.map(analyse_result_file, result_files)

    # TODO rework for multiprocessing-style result analysis
    for user, results, pval, stat in globallyViableParams:
        print(f"Getting pval<{pval}, corr>{stat} for {user}: {results}")
        print()
        print()
    

def analyse_result_file(filepath:str, season:int=1) -> (str, list[Result], float, float):
    '''
    Analyses results in a file at `filepath` and returns…:
        - username
        - all params that are viable for all folds & against the total dataset
        - and the pval threshold at which we find those params
        - the stat threshold at which we find those params.
    '''
    # Unpickle results and pop them into a dict, where keys are players and values are relevant results.
    all_results = list()
    with open(filepath, 'rb') as result_file:
        try:
            all_results = pickle.load(result_file)
        except EOFError:
            print(f"could not read [possibly empty?] result in file {filepath}")
            all_results = []
        except Exception as e:
            print("ERR!")
            print(e)
            raise e

    pvals = [0.01, 0.02, 0.035, 0.05]
    stats = [0.5, 0.4, 0.3, 0.2]
    pval_stat_index_map = [(pval_index, stat_index) for pval_index in range(len(pvals)) for stat_index in range(len(stats))]
    sorted_pval_stat_indices = sorted(pval_stat_index_map, key=sum)
    search_param_combos = list(map(lambda indices: (pvals[indices[0]], stats[indices[1]]), sorted_pval_stat_indices))

    username = filepath.split('/')[-1].split('-')[0]

    all_games = None

    for pval, stat in search_param_combos:
        print(username, pval, stat)
        within_threshold = list()
        combinations_seen = set()
        result = None
        globally_viable_params = list()
        params_to_mutate = None
        for fold in all_results:
            within_threshold_for_fold = list()
            for result in fold:
                if all_games is None:
                    all_games = result.params.training_data + result.params.testing_data
                if params_to_mutate is None:
                    params_to_mutate = copy(result.params)
                if result.within_acceptable_bounds(pval, stat):
                    within_threshold_for_fold.append((result.params.c, result.params.curve_inflection_relative_to_numgames, result.params.prob_bored))
                    combinations_seen.add((result.params.c, result.params.curve_inflection_relative_to_numgames, result.params.prob_bored))
            within_threshold.append(within_threshold_for_fold)

        commonality = dict() # c, rgr_coeff combo mapped to how many folds they appeared above threshold
        for combination in combinations_seen:
            commonality[combination] = reduce(lambda acc, fold_res: acc + (1 if combination in fold_res else 0), within_threshold, 0)
        ranked_params_for_player = sorted(commonality.items(), key=lambda x: x[1], reverse=True)
        passing_params_for_player = filter(lambda x: x[1]>=3, ranked_params_for_player)

        # Find a param set which passes more than it fails on testing folds, and also passes on the dataset as a whole.
        globally_viable_params = list()
        for possible_viable_param_set, _ in passing_params_for_player:
            params_to_mutate.c = possible_viable_param_set[0]
            params_to_mutate.curve_inflection_relative_to_numgames = possible_viable_param_set[1]
            params_to_mutate.prob_bored = possible_viable_param_set[2]
            params_to_mutate.boredom_enabled = params_to_mutate.prob_bored != 0.0001
            params_to_mutate.testing_data, params_to_mutate.training_data = all_games, all_games
            test_against_all_player_games = params_to_mutate.run_experiment(testing=True, correlation_metric=kendalltau, season=season)
            if test_against_all_player_games.within_acceptable_bounds(pval, stat):
                globally_viable_params.append(test_against_all_player_games)
        if len(globally_viable_params) > 0:
            break

    return username, globally_viable_params, pval, stat



        


    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Loads and analyses experimental results')
    parser.add_argument('result_dirs', metavar='result_dir', nargs='+', help='a directory containing results of an experimental run in .pickle format.')
    parser.add_argument('-s', '--season', default=1)
    args = parser.parse_args()

    collect_and_analyse(args.result_dirs, args.season)

