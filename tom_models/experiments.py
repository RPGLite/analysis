from experiment_base import k_fold_by_players
from pickle import dump, load
from random import shuffle
from sys import argv
from pdsf import AspectHooks
from datetime import datetime
from scipy.stats import kendalltau, spearmanr
from os import mkdir, environ

def compare_s1_s2(s1_pickled_filename):
    with open(s1_pickled_filename, 'rb') as s1_datafile:
        s1_data = load(s1_datafile)

    s2_data = dict()
    username = s1_pickled_filename.split('-')[0]
    with AspectHooks():
        from experiment_base import change_season, mitigate_randomness, compare_with_multiple_players, get_moves_from_table

    # Apply memory optimisation fuzzer
    from aspects import fuzz_nonlocalMoveLookup
    #AspectHooks.add_fuzzer('get_moves_from_table', fuzz_nonlocalMoveLookup)

    change_season(2)
    from experiment_base import shepherd, get_games_for_players

    games = get_games_for_players([username], shepherd)
    shuffle(games)
    print("found " + str(len(games)) + " games.")


    # get the s2 folds
    folds = list()  # Format is [(training1, testing1), (training2, testing2)]
    fold_count = len(s1_data)
    performances = []
    for fold_index in range(fold_count):
        start_index = int(fold_index * len(games) / fold_count)
        end_index = int((1 + fold_index) * len(games) / fold_count)

        training = games[0:start_index]+games[end_index:len(games)]
        testing = games[start_index:end_index]
        folds.append([training, testing])

        s1_rgr = s1_data[fold_index][0][0]

        test_real, test_sim = mitigate_randomness(compare_with_multiple_players,
                                                  s1_rgr,  # Should this be the best rgr found, not the one found for each original fold?
                                                  players=[username],
                                                  games=testing,
                                                  iterations=10000,
                                                  print_progress=False)

        performances.append([s1_rgr, kendalltau(test_real, test_sim).pvalue, test_real, test_sim, testing])
        print(performances[-1])

    with open(username + '-s2_test.pickle', 'wb') as outfile:
        dump(performances, outfile)


def single_player_annealing_to_rgr(username, **kwargs):
    '''
    Finds a good RGR for simulating the given user playing S1.
    Grid-searches for a good rgr, validates via k-fold validation.
    Fixes the simulated game iterations at 5,000 simulated games.
    :param username: A string representing a real-world user
    :return: the RGR we find best represents that user with grid-searched optimisation applied via k-fold validation
    '''
    with AspectHooks():
        from experiment_base import k_fold_by_players, get_moves_from_table

    # Apply memory optimisation fuzzer
    from aspects import fuzz_nonlocalMoveLookup
    #AspectHooks.add_fuzzer('get_moves_from_table', fuzz_nonlocalMoveLookup)

    # TODO not yet finished --- unclear whether spearmanr has the correct shape here (think it returns two values?!?!?)
    if 'correlation_metric' in kwargs:
        correlation_metric = kwargs['correlation_metric']
    else:
        correlation_metric = lambda real, sim: kendalltau(real, sim)
        if environ.get("USE_RHO") is not None:
            correlation_metric = lambda real, sim: spearmanr(real, sim)

    return k_fold_by_players(players=[username],
                             fold_count=5,
                             depth=4,
                             print_progress=False,
                             iterations=5000,
                             correlation_metric=correlation_metric,
                             **kwargs)

if __name__ == "__main__":

    # TODO s2 is not set up for ktau vs spearman
    if argv[1] == 's2':
        for datfile in argv[2:]:
            compare_s1_s2(datfile)

    else:
        for username in argv[1:]:
            # TODO: make note of the model of learning being applied in filename, apply
            # aspects here.
            timestamp = datetime.now().replace(minute=0, second=0, microsecond=0).isoformat()
            try:
                mkdir(timestamp + "_season1")
            except:
                pass # Folder probably already exists
            with open(timestamp + "/" + username + "-generated-" + datetime.now().isoformat() + '.pickle', 'wb') as outputfile:
                dump(single_player_annealing_to_rgr(username=username), outputfile)
