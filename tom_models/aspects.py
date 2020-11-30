from tom_models.base_model import get_opponent, Knight, Archer, Wizard, Rogue, Healer, Barbarian, Gunner, Monk
from random import random
from helper_fns import chars


#=== begin ancillary code necessary for the aspects to work — these can be moved into another package...

def games_played_by(player, environment):
    if 'played by' not in environment or player not in environment['played by']:
        return 0
    return environment['played by'][player]

# Order matters for comparison's sake, so if the order of a charpair is backwards, we need to swap them.
# We check order by looking up their precendence in the char_ordering dictionary (lowest wins.)
char_ordering = {
    'K': 0,
    'A': 1,
    'W': 2,
    'R': 3,
    'H': 4,
    'M': 5,
    'B': 6,
    'G': 7
}

#=== end ancillary code necessary for the aspects to work


# aspects
def update_confidence_model(player, environment):

    sigmoid_initial_confidence = environment['special vals']['sigmoid initial confidence']

    if 'confidence' not in environment: environment['confidence'] = dict()
    y = environment['confidence'].get(player, sigmoid_initial_confidence)
    if environment['special vals']['sigmoid type'] == "logistic":
        # REGULAR LOGISTIC ("Verhulst 1845, 1847")
        environment['confidence'][player] = y + ( environment['special vals']['rgr'] * y * (1-y) )

    elif 'birch' in environment['special vals']['sigmoid type']:
        k = 1  # upper asymptote
        a = environment['special vals']['rgr']

        if environment['special vals']['sigmoid type'] == "birch logistic":
            # BIRCH LOGISTIC
            c = 1  # for logistic curve
            environment['confidence'][player] = y + a * y * (k - y) / (k - y + c * y)

        elif environment['special vals']['sigmoid type'] == "birch exponential":
            # BIRCH EXPONENTIAL
            c = 0  # for exponential curve

        elif environment['special vals']['sigmoid type'] == "birch controlled":
            # BIRCH but with the curve value set specifically
            c = environment['special vals']['birch c']

        else:
            # birch, but not specified which one
            raise Exception("Birch equation used, but no specific equation requested")

        # Same equation for any of these
        environment['confidence'][player] = y + a * y * (k - y) / (k - y + c * y)

    return environment['confidence'][player]


def around_choosing_chars_based_on_sigmoid(next_around, target, _actor, _ctx, environment, **kwargs):
    update_confidence_model(_actor, environment)
    initial_exploration = environment['special vals']['initial_exploration']
    sigmoid_chose_to_play_winning_pair = random() < environment['confidence'][_actor]
    choice = __import__('random').choice

    if sigmoid_chose_to_play_winning_pair and games_played_by(_actor, environment) > initial_exploration:
        # set winning pair based on the teams they've seen win
        chosen_pair = choice(environment['winning teams'][_actor])
        if chars.index(chosen_pair[0]) > chars.index(chosen_pair[1]):
            chosen_pair = chosen_pair[1] + chosen_pair[0]
        pair_instances = list()
        char_class_map = {
            "K": Knight,
            "A": Archer,
            "R": Rogue,
            "W": Wizard,
            "H": Healer,
            "B": Barbarian,
            "M": Monk,
            "G": Gunner
        }
        for char in chosen_pair:
            pair_instances.append(char_class_map[char]())

        _ctx[_actor]['chars'] = pair_instances
        return pair_instances
    else:
        ret = next_around(target, _actor, _ctx, environment, **kwargs)
        pair = ""
        for char in _ctx[_actor]['chars']:
            pair += char.__class__.__name__[0]

        if chars.index(pair[0]) > chars.index(pair[1]):
            pair = pair[1] + pair[0]
        return ret


def best_move_generator(environment):
    def choose_best_moves(target, ret, *args, **kwargs):
        '''
        Replaces a set of possible moves from base_model.get_moves_from_table with the single best move, forcing that to be taken.
        Args:
            target: base_model.get_moves_from_table
            ret: the list of best moves to be taken at the game's current state
            *args: args for the function
            **kwargs: keyword args for the function

        Returns: a list containing only the best move of all moves in ret

        Note: environment here is a reference to the outer scoped 'environment' variable as passed into the function containing this func def.
        '''
        gamedoc = args[0]

        if list(map(str, gamedoc.get('moves', [None, None])[-2:])) == ['skip', 'skip']:
            return ret

        sorted_moves = sorted(ret.items(), key=lambda move: -move[1])
        return {sorted_moves[0][0]: sorted_moves[0][1]}
    return choose_best_moves

def record_simulated_choices(target, ret, players, environment, **kwargs):
    # Get a reference to the simulated choices list, and add it to the environment if it doesn't exist.
    if 'simulated_choices' not in environment:
        environment['simulated_choices'] = list()
    simulated_choices = environment['simulated_choices']

    completed_game = environment['games'][-1]

    # The pairs chosen by the players
    char_pairs = [completed_game[player]['chars'] for player in completed_game['players']]

    # Changing the pairs chosen into two-letter forms as per RPGLite's backend, such as KA for (Knight, Archer) pair
    char_pairs = map(lambda pair: pair[0].__class__.__name__[0] + pair[1].__class__.__name__[0], char_pairs)

    # Order matters for comparison's sake, so if the order is backwards, swap them. We check order by looking up their precendence in the char_ordering dictionary (lowest wins.)
    char_pairs = list(map(lambda pair: pair if char_ordering[pair[0]] < char_ordering[pair[1]] else pair[1] + pair[0], char_pairs))
    for pair in char_pairs:
        simulated_choices.append(pair)


def record_player_sees_winning_team(target, ret, players, environment, **kwargs):
    try:
        if 'winning teams' not in environment:
            environment['winning teams'] = dict()

        winning_pair = ""
        for c in environment['games'][-1]["winning player"]:
            winning_pair += c.__class__.__name__[0]

        for actor in players:
            if 'played by' not in environment:
                environment['played by'] = dict()

            environment['played by'][actor] = environment['played by'].get(actor, 0) + 1
            environment['winning teams'][actor] = environment['winning teams'].get(actor, list()) + [winning_pair]
    except Exception as e:
        print(e)
        import time
        time.sleep(2)
        raise(e)

def handle_player_cannot_win(_target, exception_raised, player, gamedoc, environment):
    '''
    To be applied as an exception handler on base_model.take_turn.
    A KeyError is raised if no moves are available to the player --- this happens when William has determined that
    there are no possible futures where the player in question can win!
    So, we artificially reduce their health to 0.
    '''
    if isinstance(exception_raised, KeyError) and exception_raised.__repr__().count('0') > 12:
        gamedoc[player]['chars'][0].health = 0
        gamedoc[player]['chars'][1].health = 0
        # Swap the active player so this player "takes another turn" and loses.
        gamedoc['active player'] = get_opponent(gamedoc['active player'], gamedoc, environment)
        print(exception_raised)
        return True
    elif isinstance(exception_raised, ValueError):
        print(exception_raised)
        return False
