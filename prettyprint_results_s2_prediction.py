import sys
import pickle

if __name__ == "__main__":
  username = sys.argv[1]
  filename = username + '-s2_test.pickle'
  with open(filename, 'rb') as datfile:
    data = pickle.load(datfile)
  for fold in data:
    print(username + '\tRGR: ' + str(fold[0]) + '\tpval: ' + str(fold[1]))
