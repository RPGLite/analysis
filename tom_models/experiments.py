from tom_models.experiment_base import k_fold_by_players
from pickle import dump
from sys import argv

def single_player_annealing_to_rgr(username):
    '''
    Finds a good RGR for simulating the given user playing S1.
    Grid-searches for a good rgr, validates via k-fold validation.
    Fixes the simulated game iterations at 5,000 simulated games.
    :param username: A string representing a real-world user
    :return: the RGR we find best represents that user with grid-searched optimisation applied via k-fold validation
    '''
    return k_fold_by_players(players=[username],
                             fold_count=5,
                             iterations=10000,
                             depth=4,
                             print_progress=False)

if __name__ == "__main__":
    with open(argv[1] + '.pickle', 'wb') as outputfile:
        dump(single_player_annealing_to_rgr(username=argv[1]), outputfile)