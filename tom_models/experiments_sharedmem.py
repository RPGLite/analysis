import argparse
from multiprocessing import Process, Manager, Pool
from threading import Thread
from datetime import datetime
from sys import argv
from os import mkdir
import os
from aspects import *

hyperbolic_learning_aspects = [
        ('prelude', 'choose*', update_confidence_model),
        ('around', 'choose*', hyperbolic_character_choice_from_win_record),
        # ('around', 'generate*', around_simulation_records_prior),
        # ('around', 'choose*', around_choosing_chars_based_on_prior_distribution),
        # ('around', 'choose*', around_choosing_chars_based_on_sigmoid),
        ('encore', 'play_game', record_simulated_choices),
        ('encore', 'play_game', track_game_outcomes),
        ('encore', 'play_game', record_player_sees_winning_team),
        ('encore', 'get_moves_from_table', choose_best_moves),
        ('error_handler', 'take_turn', handle_player_cannot_win),
]
sigmoid_learning_aspects = [
        ('prelude', 'choose*', update_confidence_model),
        # ('around', 'choose*', hyperbolic_character_choice_from_win_record),
        ('around', 'generate*', around_simulation_records_prior),
        # ('around', 'choose*', around_choosing_chars_based_on_prior_distribution),
        ('around', 'choose*', around_choosing_chars_based_on_sigmoid),
        ('encore', 'play_game', record_simulated_choices),
        ('encore', 'play_game', track_game_outcomes),
        ('encore', 'play_game', record_player_sees_winning_team),
        ('encore', 'get_moves_from_table', choose_best_moves),
        ('error_handler', 'take_turn', handle_player_cannot_win),
]
prior_distrib_learning_aspects = [
        ('prelude', 'choose*', update_confidence_model),
        # ('around', 'choose*', hyperbolic_character_choice_from_win_record),
        ('within', 'choose*', fuzz_learning_by_prior_distribution),
        # ('around', 'generate*', around_simulation_records_prior),
        # ('around', 'choose*', around_choosing_chars_based_on_prior_distribution),
        # ('around', 'choose*', around_choosing_chars_based_on_sigmoid),
        ('encore', 'play_game', record_simulated_choices),
        ('encore', 'play_game', track_game_outcomes),
        ('encore', 'play_game', record_player_sees_winning_team),
        ('encore', 'get_moves_from_table', choose_best_moves),
        ('error_handler', 'take_turn', handle_player_cannot_win),
]


def dump_experimental_result(username, outputfilename, advice_key, sigmoid_control, verbose=False, *args, **kwargs):
    import base_model
    from pickle import dump
    from experiments import single_player_annealing_to_rgr

    kwargs.update({'print_debuglines': verbose})
    if isinstance(sigmoid_control, int) or isinstance(sigmoid_control, float):
        kwargs.update({'birch_c': sigmoid_control})

    advice = learning_models[advice_key]

    with open(outputfilename, 'wb') as outputfile:
        dump(single_player_annealing_to_rgr(username=username, advice=advice, *args, **kwargs), outputfile)
    print(f"Dumped contents for {username}")

if __name__ == "__main__":

    timestamp = datetime.now().replace(second=0, microsecond=0).isoformat()

    # Parse experiment arguments
    parser = argparse.ArgumentParser(prog='RpgliteAnnealingExperiments',
           description="Fits parameters to a provided list of players to produce realistic datasets of RPGLite play.")
    parser.add_argument("players",
                        help="Name of player to run experiment for",
                        nargs="+",
                        metavar="username")
    parser.add_argument("--optimisation",
                        default="anneal_c_rgr")
    parser.add_argument('--learn_with',
                        help="IDs of learning models to run experiments for",
                        nargs='+',
                        required=True,
                        dest="learning_models",
                        metavar="learning_model")
    parser.add_argument("-d", "--result_dir", nargs='?', default=timestamp)
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    learning_models = {
        'sigmoid_learning_curve': sigmoid_learning_aspects,
        'hyperbolic_learning': hyperbolic_learning_aspects,
        'prior_distribution': prior_distrib_learning_aspects,
    }

    try:
        mkdir(args.result_dir)
    except Exception as e:
        print(e)
        pass # Folder probably already exists

    with Pool(12, initializer=lambda : os.nice(-20)) as pool:
        experiment_procs = list()
        for expname in args.learning_models:
            if expname not in learning_models.keys():
                print(f"Valid learning models are: {', '.join(learning_models.keys())}")
                exit()
            print(f"Setting up experiments with {expname}")

            try:
                mkdir(args.result_dir + f"/{expname}")
            except Exception as e:
                print(e)
                pass # Folder probably already exists

            for sigmoid_control in [1, 2, 0.5] if args.optimisation == 'old_grid' else ['annealed']:
                print(f"Setting up experiments with birch curve control: {sigmoid_control}")

                for username in args.players:
                    outputfilename = args.result_dir + f"/{expname}/" + username + f"-birchc_{sigmoid_control}-s1.pickle"
                    experiment_procs.append(pool.apply_async(dump_experimental_result,
                                                             args=(username, outputfilename, expname, sigmoid_control, args.verbose),
                                                             kwds={'optimisation': args.optimisation}))

        # Make sure all experiments are complete before closing pool.

        # catch exception if results are not ready yet
        finished = False
        while not finished:
            try:
                ready = [exp.ready() for exp in experiment_procs]
                successful = [exp.successful() for exp in experiment_procs]
                finished = True
            except Exception:
                pass
        # raise exception reporting exceptions received from workers
        if all(ready) and not all(successful):
            raise Exception(f'Workers raised following exceptions {[exp._value for exp in experiment_procs if not exp.successful()]}')