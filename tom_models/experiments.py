from tom_models.experiment_base import k_fold_by_players, kendalltau

def single_player_annealing_to_rgr(username):
    '''
    Finds a good RGR for simulating the given user playing S1.
    Grid-searches for a good rgr, validates via k-fold validation.
    Fixes the simulated game iterations at 5,000 simulated games.
    :param username: A string representing a real-world user
    :return: the RGR we find best represents that user with grid-searched optimisation applied via k-fold validation
    '''
    print(max(k_fold_by_players(players=[username],
                            fold_count=5,
                            iterations=5000,
                            depth=2,
                            # iterations=30*len(group_games),
                            # correlation_metric=lambda x: kendalltau(x).pvalue,
                            # games=group_games,
                            print_progress=True)))

if __name__ == "__main__":
    print(single_player_annealing_to_rgr(username='creilly1'))