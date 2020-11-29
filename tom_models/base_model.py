# from .middleware import *
from functools import partial
from random import sample, choice, random

'''
This module is a simulation tool for RPGLite.
This is a base model that is a kind of prediction about behaviour; it's amended by other modules (to be written).


'''
# Steps for play:
# Assume a match has been made.
# P1 chooses characters
# P2 chooses characters
# Flip a coin for first player
# while not done:
#   active player makes optimal move
#   flip active player

season = 1

class Move:
    def __init__(self, attacker=None, targeted_rolls=None, extras=None, movestring=""):
        self.attacker = attacker
        self.targeted_rolls = targeted_rolls
        self.extras = extras if extras is not None else dict()
        self.movestring = movestring

        if self.movestring and self.attacker is None:
            self.construct_from_movestring()

    @classmethod
    def construct_from_movestring(cls, gamedoc, movestring):

        if movestring == 'skip':
            return skip_move

        segments = movestring.split("_")
        player_chars = gamedoc[gamedoc['active player']]['chars']
        opp_chars = get_opponent_chars(gamedoc['active player'], gamedoc, None)

        attacker = player_chars[0] if player_chars[0].__class__.__name__[0] == segments[0] else player_chars[1]
        targets_to_process = segments[1:]
        if attacker.__class__ == Healer:
            target_letter = targets_to_process[0][0]
            target = opp_chars[0] if opp_chars[0].__class__.__name__[0] == target_letter else opp_chars[1]
            targeted_rolls = [(target, random())]

            extras = dict()
            if len(targets_to_process[0]) > 1:
                healed_letter = targets_to_process[0][1]
                char_to_heal = player_chars[0] if player_chars[0].__class__.__name__[0] == healed_letter else player_chars[1]
                extras = {'heal': [char_to_heal]}

            return cls(attacker, targeted_rolls, extras=extras, movestring=movestring)

        if attacker.__class__ == Archer:
            targets = []
            for char in targets_to_process:
                target = opp_chars[0] if opp_chars[0].__class__.__name__[0] == char else opp_chars[1]
                targets.append((target, random()))
            return cls(attacker, targets, movestring=movestring)

        # Reasonably ordinary character so no special treatment.
        target = opp_chars[0] if opp_chars[0].__class__.__name__[0] == targets_to_process[0] else opp_chars[1]
        roll = random()

        extras = dict()
        if attacker.__class__ == Wizard:
            extras['stun'] = [target]
        if attacker.__class__ == Monk:
            extras['take_turn_again'] = attacker.damage(target, roll) > 0

        return cls(attacker, [(target, roll)], extras, movestring=movestring)

    @classmethod
    def best_move(cls, gamedoc):
        moves_in_state = get_moves_from_table(gamedoc)
        best_move = sorted(moves_in_state.items(), key=lambda m: -m[1])[0][0]
        return cls.construct_from_movestring(gamedoc, best_move)

    def execute(self, _actor, _ctx, _env):
        if self.attacker is None:
            return
        for target, roll in self.targeted_rolls:
            damage = self.attacker.damage(target, roll)
            target.health = max(0, target.health - damage)

        for key, pertinent_info in self.extras.items():
            if key == 'stun':
                for target in pertinent_info:
                    target.is_stunned = (damage > 0)
            if key == 'heal':
                for target in pertinent_info:
                    target.health = target.health if damage == 0 else min(target.max_health, target.health + 1)

            if key == 'take_turn_again' and pertinent_info is True:
                _ctx['active player'] = get_opponent(_actor, _ctx, _env)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if self.attacker is None:
            return 'skip'

        return self.attacker.__class__.__name__ + ' hit ' + ', '.join(map(lambda tr: tr[0].__class__.__name__ + '(' + str(tr[1])[2:4] + ')', self.targeted_rolls))

skip_move = Move(None, None)


class Game(dict):
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        out = 'p1:\t' + ', '.join(list(map(lambda c: c.__class__.__name__ + ":" + str(c.health), self[self['players'][0]]['chars'])))
        out += '\n'
        out += 'p2:\t' + ', '.join(list(map(lambda c: c.__class__.__name__ + ":" + str(c.health), self[self['players'][1]]['chars'])))
        out += '\n\n'
        return out


class Character:
    @property
    def is_alive(self):
        return self.health > 0

    def make_move(self, _actor, _ctx, _env):
        targets = self.select_targets(_actor, _ctx, _env)

        return Move(self, targets)

    def select_targets(self, _actor, _ctx, _env):
        '''
        Returns a list of tuples, with two elements. Tuples represent rolls against targets. The first element of a tuple is the target; the second is the roll.
        '''
        targets = [(choice(list(filter(lambda c: c.is_alive, get_opponent_chars(_actor, _ctx, _env)))), random())]
        return targets


class Knight(Character):
    max_health = 10

    def __init__(self):
        self.is_stunned = False
        self.health = self.max_health
        self.acc = 0.6 if season == 1 else 0.8
        self.damage = lambda target, roll: 0 if roll > self.acc else (4 if season == 1 else 3)


class Archer(Character):
    max_health = 8 if season == 1 else 9

    def __init__(self):
        self.is_stunned = False
        self.health = self.max_health
        self.acc = 0.85 if season == 1 else 0.8
        self.damage = lambda target, roll: 0 if roll > self.acc else 2

    def select_targets(self, _actor, _ctx, _env):
        targets = [(t, random()) for t in filter(lambda c: c.is_alive, get_opponent_chars(_actor, _ctx, _env))]
        return targets

class Rogue(Character):
    max_health = 8

    def __init__(self):
        self.is_stunned = False
        self.health = self.max_health
        self.acc = 0.75 if season == 1 else 0.7
        self.damage = lambda target, roll: 0 if roll > self.acc else 3 if target.health > 5 else target.health


class Healer(Character):
    max_health = 10 if season == 1 else 9

    def __init__(self):
        self.is_stunned = False
        self.health = self.max_health
        self.acc = 0.85 if season == 1 else 0.9
        self.damage = lambda target, roll: 0 if roll > self.acc else 2

    def make_move(self, _actor, _ctx, _env):
        move = super(Healer, self).make_move(_actor, _ctx, _env)

        # Skip this if we don't damage
        if self.damage(*move.targeted_rolls[0]) == 0:
            return move

        own_alive_characters = list(filter(lambda c: c.is_alive, _ctx[_actor]['chars']))
        alive_damaged_chars = list(filter(lambda c: c.health < c.max_health, own_alive_characters))

        if len(alive_damaged_chars) == 0:
            return move

        to_heal = choice(alive_damaged_chars)
        move.extras['heal'] = [to_heal]

        return move


class Wizard(Character):
    max_health = 8

    def __init__(self):
        self.is_stunned = False
        self.health = self.max_health
        self.acc = 0.85
        self.damage = lambda target, roll: 0 if roll > self.acc else 2
        
    def make_move(self, _actor, _ctx, _env):
        move = super(Wizard, self).make_move(_actor, _ctx, _env)

        # Skip this if we don't damage
        if self.damage(*move.targeted_rolls[0]) == 0:
            return move

        move.extras['stun'] = list(map(lambda tr: tr[0], move.targeted_rolls))

        return move


class Barbarian(Character):
    max_health = 10 if season == 1 else 9

    def __init__(self):
        self.is_stunned = False
        self.health = self.max_health
        self.acc = 0.75 if season == 1 else 0.7
        self.damage = lambda target, roll: 0 if roll > self.acc else 3 if self.health > 4 else 5


class Monk(Character):
    max_health = 7

    def __init__(self):
        self.is_stunned = False
        self.health = self.max_health
        self.acc = 0.8 if season == 1 else 0.75
        self.damage = lambda target, roll: 0 if roll > self.acc else 1

    def make_move(self, _actor, _ctx, _env):
        move = super(Monk, self).make_move(_actor, _ctx, _env)

        # Skip this if we don't damage
        if self.damage(*move.targeted_rolls[0]) == 0:
            return move

        move.extras['take_turn_again'] = True
        return move


class Gunner(Character):
    max_health = 8

    def __init__(self):
        self.is_stunned = False
        self.health = self.max_health
        self.acc = 0.8 if season == 1 else 0.7
        self.damage = lambda target, roll: 1 if roll > self.acc else 4


characters = [Knight,
              Archer,
              Rogue,
              Healer,
              Wizard,
              Barbarian,
              Monk,
              Gunner]

'''
Some notes:

Contexts are game documents. They have some useful fields and follow this structure:
{
    <player object>: {dictionary of information about that player, such as 'chars' for characters chosen}
    "active player": int representing the index of "players" for the currently active player.
    "players": [<player object for p1>, <player object for p2>]
    "moves": [list of moves as strings]
}

'''

# ========== UTILITY FUNCTIONS

def get_opponent(_actor, _context, _env):
    return _context['players'][0] if _context["players"][1] == _actor else _context['players'][1]

def get_opponent_chars(_actor, _context, _env):
    return _context[get_opponent(_actor, _context, _env)]['chars']

def produce_state_string(gamedoc):
    '''
    format to produce is:
    1,0,0,0,0,0,1,0,7,0,0,0,0,0,0,0,1,0,0
    (turn,p1K,p1A,p1W,p1R,p1H,p1M,p1B,p1G,p1_stun,p2K,p2A,p2W,p2R,p2H,p2M,p2B,p2G,p2_stun)
    '''

    player = gamedoc["active player"]
    opp = get_opponent(player, gamedoc, None)

    player_chars = gamedoc[player]['chars']
    opp_chars = gamedoc[opp]['chars']

    state_tuple = [1]  # turn is always 1...
    ordering = [Knight,
                Archer,
                Wizard,
                Rogue,
                Healer,
                Monk,
                Barbarian,
                Gunner]

    # Calculate the player component of the state tuple
    healths = [0]*8
    health_index_1 = ordering.index(player_chars[0].__class__)
    health_index_2 = ordering.index(player_chars[1].__class__)
    stun_index = health_index_1 + 1 if player_chars[0].is_stunned \
        else health_index_2 + 1 if player_chars[1].is_stunned \
        else 0
    healths[health_index_1] = player_chars[0].health
    healths[health_index_2] = player_chars[1].health
    healths.append(stun_index)
    state_tuple += healths

    # Calculate the opp component of the table
    opp_healths = [0]*8
    health_index_1 = ordering.index(opp_chars[0].__class__)
    health_index_2 = ordering.index(opp_chars[1].__class__)
    stun_index = health_index_1 + 1 if opp_chars[0].is_stunned \
        else health_index_2 + 1 if opp_chars[1].is_stunned \
        else 0
    opp_healths[health_index_1] = opp_chars[0].health
    opp_healths[health_index_2] = opp_chars[1].health
    opp_healths.append(stun_index)
    state_tuple += opp_healths

    state_string = str(state_tuple)[1:-1].replace(' ', '')
    return state_string

movefile_cache = dict()


def add_to_movefile_cache(filename):
    moves_to_cache = dict()
    # process file
    with open(filename, 'r') as movefile:
        for line in movefile.readlines():
            separator_index = line.index(':')
            statestring = line[:separator_index]
            unparsed_state_map = line[separator_index+2:-2] # Skip the colon, and both the curly braces on the unparsed dict, and the newline char at the end
            mapping = dict()
            for statepair in unparsed_state_map.split(','):
                segments = statepair.split(':')
                mapping[segments[0]] = float(segments[1])

            moves_to_cache[statestring] = mapping
    movefile_cache[filename] = moves_to_cache
    return moves_to_cache


def get_moves_from_table(gamedoc):
    state_string = produce_state_string(gamedoc)
    ordering = [Knight,
                Archer,
                Wizard,
                Rogue,
                Healer,
                Monk,
                Barbarian,
                Gunner]

    player_chars = gamedoc[gamedoc['active player']]['chars']
    player_chars = sorted(player_chars, key=lambda c: ordering.index(c.__class__))
    filename = "../lookupV2/season" + str(season) + "/" + "".join(map(lambda c: c.__class__.__name__[0], player_chars)) + '.txt'

    all_moves = movefile_cache.get(filename, None)
    if all_moves is None:
        all_moves = add_to_movefile_cache(filename)

    moves_in_state = all_moves[state_string]
    return moves_in_state

# ========== MAIN MODEL CODE


def choose_chars(_actor, _context, _env):
    if _actor not in _context:
        _context[_actor] = dict()

    chars_chosen = sample(characters, 2)
    _context[_actor]['chars'] = [c() for c in chars_chosen]  # We've chosen classes, so construct an instance of each choice.

def set_first_player(_actor, _context, _env):
    _context['active player'] = _context['players'][choice([0, 1])]

def take_turn(_actor, _context, _env):
    possible_turns = list(map(lambda x: Move.construct_from_movestring(_context, x), get_moves_from_table(_context)))
    move = choice(possible_turns)
    move.execute(_actor, _context, _env)

    # un-stun all of this player's characters
    for char in _context[_actor]['chars']:
        char.is_stunned = False

    _context['moves'].append(move)

def play_game(players, environment, choices=None, first_player=None, print_moves=False):
    gamedoc = Game()
    gamedoc['moves'] = list()
    gamedoc['players'] = players

    if 'games' not in environment:
        environment['games'] = list()
    environment['games'].append(gamedoc)

    for player in players:
        gamedoc[player] = dict()

    # choose chars
    if choices is None:
        for player in players:
            choose_chars(player, gamedoc, environment)
    else:
        gamedoc[players[0]]['chars'] = choices[0]
        gamedoc[players[1]]['chars'] = choices[1]


    if first_player is None:
        set_first_player(None, gamedoc, environment)
    else:
        gamedoc['active player'] = first_player

    def gameover():
        p1_exhausted = len(list(filter(lambda p: p.is_alive, gamedoc[players[0]]['chars']))) == 0
        p2_exhausted = len(list(filter(lambda p: p.is_alive, gamedoc[players[1]]['chars']))) == 0
        return p1_exhausted or p2_exhausted

    while not gameover():
        take_turn(gamedoc['active player'], gamedoc, environment)
        gamedoc['active player'] = get_opponent(gamedoc['active player'], gamedoc, environment)

    gamedoc['winning player'] = get_opponent_chars(gamedoc['active player'], gamedoc, environment)

    if print_moves:
        print(gamedoc['moves'][-1])
        print(gamedoc)


games_to_play = 1
if __name__ == "__main__":
    environment = dict()
    players = ['x', 'y']
    for i in range(games_to_play):
        play_game(players, environment)



