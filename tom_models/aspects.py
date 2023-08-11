from base_model import get_opponent, Knight, Archer, Wizard, Rogue, Healer, Barbarian, Gunner, Monk
from scipy.stats import powerlaw
from random import random, shuffle, choice
from helper_fns import chars
import sys
import inspect
import ast


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
def update_confidence_model(_target, player, _game, environment):

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
        #print(exception_raised)
        return True
    elif isinstance(exception_raised, ValueError):
        print(exception_raised)
        return False
    else:
        print(exception_raised)
        return False


def track_game_outcomes(_target, ret, players, environment, counts_opponent=True, **kwargs):
    '''
    Aspect applying _after_ `play_game` to record the wins and losses each player observes for each charaterpair.
    Tracks it in environment['win record'][<player>][<charpair>] = [list of bools where True represents a win, ordered from most to least recent]
    :param _target:
    :param actor:
    :param gamedoc:
    :param environment:
    :param kwargs:
    :return:
    '''
    try:
        gamedoc = environment['games'][-1]
        losing_pair = ""
        losing_player = gamedoc["active player"]
        for c in gamedoc[losing_player]['chars']:
            losing_pair += c.__class__.__name__[0]

        winning_pair = ""
        winning_player = players[0] if players[0] is not losing_player else players[1]
        for c in gamedoc["winning player"]:
            winning_pair += c.__class__.__name__[0]

        initialise_win_record(winning_player, environment)
        initialise_win_record(losing_player, environment)

        # TODO: do I track pairs, or chars? currently pairs.
        pairs = list()
        for char1_index in range(8):
            for char2_index in range(char1_index+1, 8):
                pair = chars[char1_index] + chars[char2_index]
                pairs.append(pair)  # keep track of each valid pair for the below loop

        # Record what the players see, for each charpair
        for pair in pairs:
            winner_to_add = True if pair == winning_pair else (False if pair == losing_pair and counts_opponent else None)
            loser_to_add = False if pair == losing_pair else (True if pair == winning_pair and counts_opponent else None)

            environment['win record'][winning_player][pair].append(winner_to_add)
            environment['win record'][losing_player][pair].append(loser_to_add)

    except Exception as e:
        import sys
        print(e.__str__() + " on line {}".format(sys.exc_info()[-1].tb_lineno))

def initialise_win_record(player, environment):
    if 'win record' not in environment:
        environment['win record'] = dict()

    if player not in environment['win record']:
        environment['win record'][player] = dict()
        for char1_index in range(8):
            for char2_index in range(char1_index + 1, 8):
                pair = chars[char1_index] + chars[char2_index]
                environment['win record'][player][pair] = list()


def hyperbolic_score(char_record, discounting_degree, unplayed_coefficient=0):
    '''
    Calculates the hyperbolic decay of an observed win record.
    Wins are worth 1 point, losses -1 points, a game where the character is unused 0 points.
    Points are multiplied by a decaying coefficient for hyperbolic discounting.

    :param char_record: a list of True for win, False for lose, and None for unplayed, ordered most to least recently played.
    :param discounting_degree: dictates how quickly we decay. "How quickly do we forget past performance?"
    :param unplayed_coefficient: Defines how we treat games where a character wasn't played, by changing how much "time" "passes". This is to resolve the question: when a character isn't played, how much does a player "forget" how good they were? In hyperbolic discounting terms, how much delay does a lack of an observation entail? Unplayed games are worth a score of 0, but the change in delay used for calculating their hyperbolic coefficient (and the coefficient of every other game after an unplayed one) is what matters to us here. At 0, we ignore unplayed games, and no "time" passes. At 1, we record time as it truely passed and record the same degree of delay as we would a win/lose. Between these, we treat them as a _percentage_ of a game played. Can be used to measure growing disinterest / forgetfulness.
    :return: A hyperbolic-discounted score for the provided record.
    '''
    try:
        score_values = list()
        delay = 0

        outcome_score_mapping = {
            True: 1,
            False: -1,
            None: 0
        }
        outcome_delay_mapping = {
            True: 1,
            False: 1,
            None: unplayed_coefficient  # This is how we track how time is recorded to "change" when a character isn't used.
        }

        for outcome in char_record:
            score = outcome_score_mapping[outcome]
            discounted_score = score * (1/(1+discounting_degree*delay))
            score_values.append(discounted_score)
            delay += outcome_delay_mapping[outcome]

        return sum(score_values)
    except Exception as e:
        import sys
        print(e.__str__() + " on line {}".format(sys.exc_info()[-1].tb_lineno))

def hyperbolic_character_choice_from_win_record(next_around, target, actor, gamedoc, environment, discounting_degree=1, score_type='hyperbolic', **kwargs):

    try:
        initialise_win_record(actor, environment)

        score_system_map = {
            'hyperbolic': hyperbolic_score
        }
        score = score_system_map[score_type]

        initial_exploration = environment['special vals']['initial_exploration']
        sigmoid_chose_to_play_winning_pair = random() < environment['confidence'][actor]

        # NOTE: do I want to keep the confidence model in here? If so, below snippets go between this `if` and `else`
        if sigmoid_chose_to_play_winning_pair and games_played_by(actor, environment) > initial_exploration:

            char_scores = dict()
            for pair in environment['win record'][actor]:
                char_scores[pair] = score(environment['win record'][actor][pair], discounting_degree)

            cumulative_distribution = powerlaw(1.5).cdf  # increase 1.5 for a more extreme split

            buckets = [1/n for n in range(1, len(char_scores)+1)]

            # We're going to sort and want pairs with the same score to fall in a random order, so we shuffle here
            pairs_and_scores = list(char_scores.items())
            shuffle(pairs_and_scores)

            sorted_pair_score_tuples = sorted(pairs_and_scores, key=lambda ps_tuple: ps_tuple[1])

            bucket_pair_mapping = [(cumulative_distribution(buckets[i]), sorted_pair_score_tuples[i][0]) for i in range(len(buckets))]  # maps a bucket's cutoff in the probability distribution to its charpair

            choice_limit = random()
            choice = bucket_pair_mapping[0][1]

            for bucket_limit, pair in bucket_pair_mapping:
                if choice_limit < bucket_limit and choice is not None:
                    choice = pair

            # Now we've picked a pair! Return correctly.
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
            for char in choice:
                pair_instances.append(char_class_map[char]())

            gamedoc[actor]['chars'] = pair_instances
            return pair_instances
        else:
            return next_around(target, actor, gamedoc, environment, **kwargs)


    except Exception as e:
        import sys
        print(e.__str__() + " on line {}".format(sys.exc_info()[-1].tb_lineno))

def around_simulation_records_prior(next_around, target, *args, **kwargs):
    game_frame = 0
    while 'games' not in sys._getframe(game_frame).f_locals:
        game_frame += 1


    games = sys._getframe(game_frame).f_locals['games']
    players = sys._getframe(game_frame).f_locals['players']

    from experiment_base import find_distribution_of_charpairs_from_players_collective_games
    distribution = find_distribution_of_charpairs_from_players_collective_games(players, games)
    possible_choices = list()
    for pair, count in distribution.items():
        for _ in range(count):
            possible_choices.append(pair)

    prior_distribution = possible_choices

    return next_around(target, *args, **kwargs)

def around_choosing_chars_based_on_prior_distribution(next_around, target, actor, gamedoc, environment, **kwargs):
    prior_distribution_frame = 0
    stack_size = len(inspect.stack())

    while 'prior_distribution' not in sys._getframe(prior_distribution_frame).f_locals and prior_distribution_frame < stack_size:
        prior_distribution_frame += 1

    if stack_size == prior_distribution_frame:
        raise Exception("Could not find a distribution to pick from — maybe we don't record it properly, or an appropriate aspect isn't enabled??")

    prior_distribution = sys._getframe(prior_distribution_frame).f_locals['prior_distribution']
    pair = choice(prior_distribution)

    # Now we've picked a pair! Return correctly.
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
    for char in pair:
        pair_instances.append(char_class_map[char]())

    gamedoc[actor]['chars'] = pair_instances
    return pair_instances


def fuzz_nonlocalMoveLookup(steps, gamedoc, *args, **kwargs):
    '''
    A fuzzer on get_moves_from_table which replaces the lookup for cached moves
    with a call to a server which performs the lookup and serves responses.
    Greatly reduces the memory footprint of an experiment.
    '''
    import_requests_ast = ast.parse("import requests")
    get_move_ast = ast.parse('moves_in_state = requests.get(f"http://127.0.0.1:8000/?state_string={state_string}&filename={filename}").json()')
    steps = steps[:6] + [import_requests_ast.body[0], get_move_ast.body[0]] + steps[8:]
    return steps

