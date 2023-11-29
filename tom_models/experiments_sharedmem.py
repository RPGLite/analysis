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
        ('prelude', 'choose*', prelude_before_learning_by_prior_distribution),
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

# To avoid loading shepherd cache in this process, calculated the count of games played in each season for each player ahead of time.
s1_gamecount_by_username = {'Ellen': 298, 'BestWilliam': 36, 'Sabotage': 49, 'Luca1802': 67, 'Frp97': 124, 'Mageofheart': 30, 'demander': 31, 'Gerr': 32, 'Beth': 52, 'georgedo': 171, 'eggface': 68, 'CalHaribo': 41, 'Marta': 48, 'BabaG': 1, 'Etess': 123, 'Super_Ia': 6, 'Connman96': 3, 'alan': 65, 'Jules_217': 13, 'cats': 19, 'DoctorW': 74, 'creilly2': 149, 'sidb': 25, 'pool27': 100, 'apropos0': 256, 'charlotte': 81, 's_c_bear': 1, 'LewisDyer': 19, 'ruadh_mor': 30, 'Paulverise': 20, 'creilly1': 379, 'Rarno': 19, 'TheMaster': 12, 'Cm83': 3, 'Kjreid': 15, 'JoeExotic': 5, 'Suzs': 3, 'Shanys': 7, 'zShi': 2, 'superrad': 1, 'Mando': 6, 'Alliyana': 22, 'cute320215': 8, 'ECDr': 224, 'Nari': 137, 'tanini': 291, 'dalinar': 79, 'l17r': 132, 'astrospanner': 10, 'ruadh_beag': 4, 'Paddy': 139, 'EarlofSurl': 51, 'norgart': 45, 'pigeon': 30, 'Elessar': 5, 'bladestoe': 52, 'versatile': 30, 'asdf': 22, 'frick': 1, 'timri': 127, 'gummytribble': 40, 'Jamie': 256, 'cwallis': 168, 'oxocube': 1, 'kubajj': 202, 'bcslippers': 13, 'rocinante': 32, 'joanna': 1, 'RandomUser': 1, 'MarkyMark74': 4, 'whiplash': 39, 'probablyrob': 29, 'yasmin_f': 13, 'Marv_911': 3, 'Deanerbeck': 217, 'mumdoc': 2, 'DavetheRave': 23, 'MhairiM': 15, 'walshy1066': 48, 'Felix42': 13, 'elennon': 116, 'totem37': 23, 'GReat': 8, 'sophie': 53, 'sstein': 123, 'OKaemii': 28, 'jack': 66, 'Schmofe': 6, 'Fbomb': 172, 'bijtis': 8, 'meow': 29, 'umachan': 64, 'Nonni': 66, 'jonildo': 31, 'GraeChan': 8, 'mosam1311': 9, 'basta': 102, 'deathseeker': 24, 'Manakish': 46, 'Sidthesloth': 26, 'Benlog': 28, 'Atrps': 7, 'Apollogize': 12, 'Kojack': 5, 'Damian': 3, 'Kush': 2}
s2_gamecount_by_username = {'Ellen': 352, 'Paddy': 14, 'l17r': 1004, 'Kush': 3, 'basta': 145, 'apropos0': 733, 'tanini': 8, 'creilly2': 5, 'demander': 6, 'Beth': 65, 'Fbomb': 19, 'Frp97': 809, 'Luca1802': 338, 'Nari': 304, 'georgedo': 97, 'jack': 10, 'Nonni': 11, 'ECDr': 313, 'timri': 270, 'MhairiM': 7, 'deathseeker': 17, 'Atrps': 3, 'Schmofe': 2, 'Apollogize': 46, 'creilly1': 129, 'Deanerbeck': 429, 'sophie': 27, 'DavetheRave': 119, 'alan': 67, 'walshy1066': 19, 'sstein': 194, 'DoctorW': 3, 'dalinar': 69, 'Sidthesloth': 5, 'Silver': 15, 'pool27': 6, 'elennon': 64, 'rocinante': 10, 'Williscraft': 3, 'Significance': 28, 'Yogurt': 1, 'Finlad': 24, 'Jhannah': 108, 'BetterThanU': 58, 'Fudgewolf': 9, 'SGUNNER07': 5, 'aaaa': 117, 'Master4444': 19, 'Morntato': 15, 'musicalSpear': 20, 'simtsui': 2, 'stru': 3, 'Hide_on_bush': 10, 'JustJoe242': 1, '7Name1eSs': 2, 'Melonchi': 1, 'bingoboy': 1, 'Andy': 84, 'alcam456': 86, 'AethelredVS': 3, 'Fudgecakes': 8, 'CannyCaracal': 26, 'Martin': 157, 'adamski5298': 42, 'bobabell': 25, 'tickler': 27, 'AMrza99': 11, 'Chrispie111': 35, 'sophc9797': 3, 'Michael': 32, 'rowan': 14, 'chins': 55, 'jaymoney': 37, 'Jules': 35, 'LLilliputian': 48, 'Tharry0': 53, 'Ezzey': 141, 'Anakhand': 27, 'Vinc0310': 6, 'Beccccca': 230, 'Rilla_Treesp': 6, 'Baepsae': 7, 'Lavarider': 14, 'V4ssilios': 11, 'Hippodoodle': 3, 'claremcskim1': 3, 'The_big_Ali': 5, 'Frostspear': 1, 'grejurn': 1, 'Marta': 2, 'eggface': 41, 'ChrialCentre': 1, 'Kojack': 1, 'Jambo9000': 14, 'wasyl2001': 1, 'TheMaster': 3, 'BerrySauce': 86, 'MJWR': 1, 'DX13': 314, 'vinl': 54, 'Lotua': 29, 'Suzs': 1}


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
                        help="Name of player to run experiment for. If an integer is passed, runs experiment for all players who completed at least that number of games.",
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

    # Check whether an int was passed instead
    player_list = args.players
    try:
        game_limit = int(args.players[0])
        player_list = [username for username, gamecount in s1_gamecount_by_username.items() if gamecount > game_limit]
    except ValueError:
        pass

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

                for username in player_list:
                    outputfilename = args.result_dir + f"/{expname}/" + username + f"-birchc_{sigmoid_control}-s1.pickle"
                    kwargs = {'optimisation': args.optimisation}
                    if expname == 'prior_distribution':
                        kwargs.update({'test_with_no_boredom': False, 'cvals_to_explore': [1], 'inflection_point_positions': [1], 'prob_bored_to_explore': [0]})
                    experiment_procs.append(pool.apply_async(dump_experimental_result,
                                                             args=(username, outputfilename, expname, sigmoid_control, args.verbose),
                                                             kwds=kwargs))

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
