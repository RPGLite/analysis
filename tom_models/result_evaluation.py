from experiment_base import Result, ModelParameters
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
    result_map = dict()
    for filepath in result_files:
        print(filepath)
        with open(filepath, 'rb') as result_file:
            try:
                result_file.readlines()
                result = pickle.load(result_file)
            except EOFError:
                print(f"empty result in file {filepath}")
                result = []
            except Exception as e:
                print("ERR!")
                print(e)
                exit()
            print(result)

    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Loads and analyses experimental results')
    parser.add_argument('result_dirs', metavar='result_dir', nargs='+', help='a directory containing results of an experimental run in .pickle format.')
    parser.add_argument('-s', '--season', default=1)
    args = parser.parse_args()

    analyse_results(args.result_dirs, args.season)

