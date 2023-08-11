from multiprocessing import Process, Manager
from threading import Thread
from datetime import datetime
from sys import argv
from os import mkdir
import os

def dump_with_shared_memory(movefile_cache, username, outputfilename):
    import base_model
    from pickle import dump
    from experiments import single_player_annealing_to_rgr

    base_model.movefile_cache = movefile_cache

    with open(outputfilename, 'wb') as outputfile:
        dump(single_player_annealing_to_rgr(username=username), outputfile)

if __name__ == "__main__":
    timestamp = datetime.now().replace(second=0, microsecond=0).isoformat()
    try:
        mkdir(timestamp)
    except Exception as e:
        print(e)
        pass # Folder probably already exists

    experiments = dict() # maps usernames to experiment processes
    populated_movefile_cache = dict()

    # Populate movefile cache
    lookup_file_location = "../lookupV2/season1"
    for filename in os.listdir(lookup_file_location):
        print(filename)
        filepath = os.path.join(lookup_file_location, filename)
        if len(filename) == 6 and os.path.isfile(os.path.join(lookup_file_location, filename)):
            moves_to_cache = dict()
            with open(filepath, 'r') as movefile:
                for line in movefile.readlines():
                    separator_index = line.index(':')
                    statestring = line[:separator_index]
                    unparsed_state_map = line[separator_index+2:-2] # Skip the colon, and both the curly braces on the unparsed dict, and the newline char at the end
                    mapping = dict()
                    for statepair in unparsed_state_map.split(','):
                        segments = statepair.split(':')
                        mapping[segments[0]] = float(segments[1])

                    moves_to_cache[statestring] = mapping
            populated_movefile_cache[filepath] = moves_to_cache

    for username in argv[1:]:
    # TODO: make note of the model of learning being applied in filename, apply
    # aspects here.

        outputfilename = timestamp + "/" + username + "-generated-" + datetime.now().isoformat() + '.pickle'
        experiments[username] = Process(target=dump_with_shared_memory, args=(populated_movefile_cache, username, outputfilename))
        experiments[username].start()
    for experiment in experiments.values():
        experiment.join()
