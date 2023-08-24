import argparse
from multiprocessing import Process, Manager
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
        ('encore', 'get_moves_from_table', best_move_generator()),
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
        ('encore', 'get_moves_from_table', best_move_generator()),
        ('error_handler', 'take_turn', handle_player_cannot_win),
]
prior_distrib_learning_aspects = [
        ('prelude', 'choose*', update_confidence_model),
        # ('around', 'choose*', hyperbolic_character_choice_from_win_record),
        ('around', 'generate*', around_simulation_records_prior),
        ('around', 'choose*', around_choosing_chars_based_on_prior_distribution),
        # ('around', 'choose*', around_choosing_chars_based_on_sigmoid),
        ('encore', 'play_game', record_simulated_choices),
        ('encore', 'play_game', track_game_outcomes),
        ('encore', 'play_game', record_player_sees_winning_team),
        ('encore', 'get_moves_from_table', best_move_generator()),
        ('error_handler', 'take_turn', handle_player_cannot_win),
]


def dump_experimental_result(username, outputfilename, advice, sigmoid_control, *args, **kwargs):
    import base_model
    from pickle import dump
    from experiments import single_player_annealing_to_rgr

    with open(outputfilename, 'wb') as outputfile:
        dump(single_player_annealing_to_rgr(username=username, advice=advice, birch_c=sigmoid_control, *args, **kwargs), outputfile)
        # dump(single_player_annealing_to_rgr(username=username, birch_c=sigmoid_control), outputfile)

if __name__ == "__main__":

    # Parse experiment arguments
    parser = argparse.ArgumentParser(prog='RpgliteAnnealingExperiments',
           description="Fits parameters to a provided list of players to produce realistic datasets of RPGLite play.")
    parser.add_argument("players",
                        help="Name of player to run experiment for",
                        nargs="+",
                        metavar="username")
    parser.add_argument("--optimisation",
                        default="anneal_c_rgr")
    args = parser.parse_args()

    for expname, experiment_aspects in [('sigmoid learning curve', sigmoid_learning_aspects), ('hyperbolic learning', hyperbolic_learning_aspects), ('prior distribution', prior_distrib_learning_aspects)]:
    # for expname, experiment_aspects in [('hyperbolic learning', hyperbolic_learning_aspects)]:
        print(f"Setting up experiments with {expname}")
        for sigmoid_control in [1, 2, 0.5]:
        # for sigmoid_control in [1]:
            print(f"Setting up experiments with birch curve control: {sigmoid_control}")
            timestamp = datetime.now().replace(second=0, microsecond=0).isoformat()
            try:
                mkdir(timestamp)
            except Exception as e:
                print(e)
                pass # Folder probably already exists

            try:
                mkdir(timestamp + f"/{expname}")
            except Exception as e:
                print(e)
                pass # Folder probably already exists

            experiments:dict[str:Process] = dict() # maps usernames to experiment processes

            # populated_movefile_cache = dict()

            # # Populate movefile cache
            # lookup_file_location = "../lookupV2/season1"
            # for filename in os.listdir(lookup_file_location):
            #     print(filename)
            #     filepath = os.path.join(lookup_file_location, filename)
            #     if len(filename) == 6 and os.path.isfile(os.path.join(lookup_file_location, filename)):
            #         moves_to_cache = dict()
            #         with open(filepath, 'r') as movefile:
            #             for line in movefile.readlines():
            #                 separator_index = line.index(':')
            #                 statestring = line[:separator_index]
            #                 unparsed_state_map = line[separator_index+2:-2] # Skip the colon, and both the curly braces on the unparsed dict, and the newline char at the end
            #                 mapping = dict()
            #                 for statepair in unparsed_state_map.split(','):
            #                     segments = statepair.split(':')
            #                     mapping[segments[0]] = float(segments[1])

            #                 moves_to_cache[statestring] = mapping
            #         populated_movefile_cache[filepath] = moves_to_cache


            for username in args.players:
                outputfilename = timestamp + f"/{expname}/" + username + f"-birchc_{sigmoid_control}-s1.pickle"
                experiments[username] = Process(target=dump_experimental_result, args=(username, outputfilename, experiment_aspects, sigmoid_control), kwargs={'optimisation': args.optimisation})
                experiments[username].start()
                os.system(f"renice -n -20 -p {experiments[username].pid}")
            try:
                for experiment in experiments.values():
                    experiment.join()
            except Exception as err:
                print(err)
                print(f"Got exception, terminating all processes.")
                for experiment in experiments.values():
                    if not experiment.is_alive():
                        experiment.terminate()
