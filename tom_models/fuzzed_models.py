from pdsf import AspectHooks
with AspectHooks():
    from base_model import *


def only_move_is_best(target, ret, *args, **kwargs):
    '''
    Replaces a set of possible moves from base_model.get_moves_from_table with the single best move, forcing that to be taken.
    Args:
        target: base_model.get_moves_from_table
        ret: the list of best moves to be taken at the game's current state
        *args: args for the function
        **kwargs: keyword args for the function

    Returns: a list containing only the best move of all moves in ret
    '''
    sorted_moves = sorted(ret.items(), key=lambda move: -move[1])
    return {sorted_moves[0][0]: sorted_moves[0][1]}

def only_move_is_best_for_player_x(target, ret, *args, **kwargs):
    '''
    Just like only_move_is_best, but it only works if the current actor is 'x'
    Args:
        target:
        ret:
        *args:
        **kwargs:

    Returns:

    '''
    gamedoc = args[0]
    actor = gamedoc['active player']
    if actor == 'x':
        sorted_moves = sorted(ret.items(), key=lambda move: -move[1])
        return {sorted_moves[0][0]: sorted_moves[0][1]}
    return ret


BASE_APATHY = 0.1
def track_player_apathy(target, ret, *args, **kwargs):
    actor, gamedoc, _env = args
    current_apathy = gamedoc[actor].get('apathy', BASE_APATHY)
    new_apathy = apathy_model(current_apathy)
    gamedoc[actor]['apathy'] = new_apathy
    # print(produce_state_string(gamedoc))
    return ret


ELO_DEFAULT = 1200
ELO_K = 64
ELO_WIDTH = 400
def track_player_elo(target, ret, *args, **kwargs):
    '''
    To apply to play_game to track what happens at a game's completion.
    Args:
        target:
        ret:
        *args:
        **kwargs:

    Returns:

    '''

    actor, env = args
    gamedoc = env['games'][-1]
    if 'elo scores' not in env:
        env['elo scores'] = dict()
    p1_score = env['elo scores'].get(gamedoc['players'][0], ELO_DEFAULT)
    p2_score = env['elo scores'].get(gamedoc['players'][1], ELO_DEFAULT)
    p1_won = any(map(lambda char: char.health > 0, gamedoc[gamedoc['players'][0]]['chars']))

    p1_score, p2_score = update_elo(p1_score, p2_score) if p1_won else update_elo(p2_score, p1_score)

    env['elo scores'][gamedoc['players'][0]] = p1_score
    env['elo scores'][gamedoc['players'][1]] = p2_score

    print(env['elo scores'])

    return ret

def update_elo(winner_elo, loser_elo):
    """
    https://en.wikipedia.org/wiki/Elo_rating_system#Mathematical_details
    """
    expected_win = expected_result(winner_elo, loser_elo)
    change_in_elo = ELO_K * (1 - expected_win)
    winner_elo += change_in_elo
    loser_elo -= change_in_elo
    return winner_elo, loser_elo

def expected_result(elo_a, elo_b):
    """
    https://en.wikipedia.org/wiki/Elo_rating_system#Mathematical_details
    """
    expect_a = 1.0 / (1 + 10 ** ((elo_b - elo_a) / ELO_WIDTH))
    return expect_a




def cannot_skip(target, ret, *args, **kwargs):
    '''
    To be applied to get_moves_from_table
    '''
    del ret['skip']
    return ret


def apathy_model(current_apathy):
    # We're using the Birch sigmoid equation as our model of apathy. TODO: this doesn't seem to give us lovely curves in practice, tweak this.
    a = relative_growth = 0.5  # This gives us a gentler version of a logistic curve
    K = upper_asymptote = 1  # To keep this as a float
    c = max_growth_rate = 1  # For similarity with the standard logistic curve
    change_in_apathy = lambda curr: (a*curr*(K-curr))/(K-curr+c*curr)
    return current_apathy + change_in_apathy(current_apathy)


def print_and_continue_on_exception(target, exception, *args, **kwargs):
    print(exception)
    return True  # Avoids raising the exception in pdsf


class SkipIsOptimalException(Exception):
    '''
    Gets raised if we find a skip to be an optimal move.
    In this case, the best thing for the player to do is to wait, because the opponent moving puts them at an advantage.
    This typically happens with barb V barb when both other chars are dead.
    In this situation, The opponent will not want to give the player concerned an opportunity, meaning they will
    also skip. Therefore, optimal moves will generally result in a draw if skipping is optimal.
    Given this is the case, we chalk this up a draw and continue, raising an exception to effectively discard this game.

    TODO: add this game to the ENV as a draw here, for later analysis. Take the actor, gamedoc, env as __init__ parameters.
    '''
    pass


def discard_game_if_draw_state_reached(target, *args, **kwargs):
    '''To be applied to get_moves_from_table'''
    valid_moves = target(*args, **kwargs)
    if max(valid_moves.items(), key=lambda kv_pair: kv_pair[1])[0] is 'skip':
        raise SkipIsOptimalException()
    return valid_moves


games_to_play = 50
if __name__ == "__main__":
    # AspectHooks.add_around('make_move', make_optimal_move)

    AspectHooks.add_encore('get_moves_from_table', only_move_is_best_for_player_x)
    AspectHooks.add_encore('take_turn', track_player_apathy)
    # AspectHooks.add_encore('get_moves_from_table', cannot_skip)
    AspectHooks.add_encore('play_game', track_player_elo)
    AspectHooks.add_error_handler('play_game', print_and_continue_on_exception)
    AspectHooks.add_around('get_moves_from_table', discard_game_if_draw_state_reached)

    environment = dict()
    players = ['x', 'y']
    for i in range(games_to_play):
        # choices = [(Gunner(), Barbarian()), (Gunner(), Barbarian())]
        # choices[0][0].health = 0
        # choices[0][1].health = 5
        # choices[1][0].health = 0
        # choices[1][1].health = 5
        choices = None

        play_game(players, environment, choices=choices, first_player='x')

    # print(len(list(filter(lambda g: g['x']['chars'][1].health > 0, environment['games']))))
    # print(len(list(filter(lambda g: g['y']['chars'][1].health > 0, environment['games']))))

    pass


