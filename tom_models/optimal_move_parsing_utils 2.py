from .base_model import characters, Knight, Archer, Wizard, Rogue, Healer, Monk, Barbarian, Gunner
from helper_fns import full_name

def optimal_move_table():
    pickle_file = 'optimal_moves.pickle'
    try:
        with open(pickle_file, 'r') as optimal_moves:
            return optimal_moves
    except:
        # pickle doesn't exist yet. Make it, write to the file, and then return it.
        optimal_moves = dict()  # The structure of this dictionary will be {[player_char1, player_char2, opp_char1, opp_char2] -> {[pc1_health, pc2_health, oc1_health, oc2_health, p_stunned_char] -> move_string}}
        movefile_character_ordering = [Knight, Archer, Wizard, Rogue, Healer, Monk, Barbarian, Gunner]
        for char_i in range(8):
            for char_j in range(char_i+1, 8):
                curr_pair = (characters[char_i], characters[char_j])
                optimal_moves[curr_pair] = dict()

                # Get the move file
                move_file_name = characters[char_i].__name__[0] + characters[char_j].__name__ + "_optimal_moves.txt"
                with open('../lookup_tables/' + move_file_name, 'r') as movefile:
                    # populate the move table with info from the move file
                    for line in movefile.readlines():
                        line = line.split()
                        # curr player health is easy
                        pair_health = (int(line[0], int(line[1])))
                        # This is our stunned character! just the name as a string for now.
                        stun = None if line[2] == "-" else eval(full_name(line(2)))
                        # health_with_stun = int(line[0]), int(line[1]), stun

                        # TODO: get the opponent's active characters and those characters' healths.
                        opponent =







def optimal_move(gamedoc):
    raise NotImplemented()
