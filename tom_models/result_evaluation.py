from experiment_base import Result, ModelParameters
from functools import reduce
from copy import copy
from scipy.stats import kendalltau
import pathlib
import argparse
import os
import pickle

def analyse_results(result_dirs, season=1):
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
    
    # Unpickle results and pop them into a dict, where keys are players and values are relevant results.
    result_map:dict[str:list[list[Result]]] = {}
    for filepath in result_files:
        print(filepath)
        with open(filepath, 'rb') as result_file:
            try:
                result = pickle.load(result_file)
            except EOFError:
                print(f"could not read [possibly empty?] result in file {filepath}")
                result = []
            except Exception as e:
                print("ERR!")
                print(e)
                result = None
        result_map[filepath] = result

    pvals = [0.01, 0.02, 0.035, 0.05]
    stats = [0.5, 0.4, 0.3, 0.2]
    pval_stat_index_map = [(pval_index, stat_index) for pval_index in range(len(pvals)) for stat_index in range(len(stats))]
    sorted_pval_stat_indices = sorted(pval_stat_index_map, key=sum)
    search_param_combos = list(map(lambda indices: (pvals[indices[0]], stats[indices[1]]), sorted_pval_stat_indices))

    
    viable_results_for_user = dict()
    favoured_search_params_for_user = dict()
    for user, all_results in result_map.items():
        for pval, stat in search_param_combos:
            print(user, pval, stat)
            within_threshold = list()
            combinations_seen = set()
            for fold in all_results:
                within_threshold_for_fold = list()
                for result in fold:
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
            all_games = result.params.training_data + result.params.testing_data
            params_to_test = copy(result.params)
            globally_viable_params = list()
            for possible_viable_param_set, _ in passing_params_for_player:
                params_to_test.c = possible_viable_param_set[0]
                params_to_test.curve_inflection_relative_to_numgames = possible_viable_param_set[1]
                params_to_test.prob_bored = possible_viable_param_set[2]
                params_to_test.boredom_enabled = params_to_test.prob_bored != 0.0001
                params_to_test.testing_data, params_to_test.training_data = all_games, all_games
                test_against_all_player_games = params_to_test.run_experiment(testing=True, correlation_metric=kendalltau)
                if test_against_all_player_games.within_acceptable_bounds(pval, stat):
                    globally_viable_params.append(test_against_all_player_games)
            if len(globally_viable_params) > 0:
                break
        viable_results_for_user[user] = globally_viable_params
        favoured_search_params_for_user[user] = (pval, stat)

    for user in viable_results_for_user:
        results = viable_results_for_user[user]
        pval, stat = favoured_search_params_for_user[user]
        print(f"Getting pval<{pval}, corr>{stat} for {user}: {results}")
        print()
        print()


        


    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Loads and analyses experimental results')
    parser.add_argument('result_dirs', metavar='result_dir', nargs='+', help='a directory containing results of an experimental run in .pickle format.')
    parser.add_argument('-s', '--season', default=1)
    args = parser.parse_args()

    analyse_results(args.result_dirs, args.season)

