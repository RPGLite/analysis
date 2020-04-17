from pymongo import MongoClient
import pickle


connectionstring = 'mongodb://takuu.dcs.gla.ac.uk:27017'
client = MongoClient(connectionstring)
database_name = "Game_data"
db = client[database_name]
players = db["players"]
games = db["games"]
completed_games = db["completed_games"]
player_backup = db["player_backup"]
games_backup = db['games_backup']
page_hits = db['page_hits']
special_data = db['special_data']
dereferenced_games = db['dereferenced_games']


cache_filepath = 'shepherd_cache.pickle'

def clevercache():
    return_cache = dict()
    def wrapper(func):
        def _(*args, **kwargs):
            func_arg_key = (func, args, tuple(kwargs.items()))

            if func_arg_key not in return_cache:
                return_cache[func_arg_key] = func(*args, **kwargs)

            return return_cache[func_arg_key]

        return _

    def cache_clearer():
        for k in return_cache:
            del return_cache[k]

    return wrapper, cache_clearer


pure, clear_pure_cache = clevercache()


def game_doc_was_abandoned(gamedoc):
    return gamedoc.get('p1_abandon', False) or gamedoc.get('p2_abandon', False) or 'apply abandon penalty' in gamedoc['most recent activity'] or gamedoc['active_player'] == 'none'


class Shepherd:

    connectionstring = 'mongodb://takuu.dcs.gla.ac.uk:27017'
    client = MongoClient(connectionstring)
    database_name = "Game_data"
    db = client[database_name]
    players = db["players"]
    games = db["games"]
    completed_games = db["completed_games"]
    player_backup = db["player_backup"]
    games_backup = db['games_backup']
    page_hits = db['page_hits']
    special_data = db['special_data']
    dereferenced_games = db['dereferenced_games']

    outlier_bound_games_played = 0.1  # Percentage of players at the top and bottom we consider exceptions

    def __init__(self, load_cache_by_file=False):
        self.load_cache_by_file = load_cache_by_file
        self.cache = dict()
        self.database_name = "Game_data"
        self.db = client[database_name]
        self.players = db["players"]
        self.games = db["games"]
        self.completed_games = db["completed_games"]
        self.player_backup = db["player_backup"]
        self.games_backup = db['games_backup']
        self.page_hits = db['page_hits']
        self.special_data = db['special_data']
        self.dereferenced_games = db['dereferenced_games']

        self.build_fresh_cache()


    def build_fresh_cache(self):

        clear_pure_cache()

        if self.load_cache_by_file:
            with open(cache_filepath, 'rb') as cachefile:
                self.cache = pickle.load(cachefile)
        else:
            Shepherd.client = MongoClient(Shepherd.connectionstring)
            self.cache['games'] = list(self.games.find({}))
            self.cache['players'] = list(self.players.find({}))
            self.cache['completed_games'] = list(self.completed_games.find({}))
            self.cache['page_hits'] = list(self.page_hits.find({}))
            self.cache['special_data'] = list(self.special_data.find({}))
            self.cache['dereferenced_games'] = list(self.dereferenced_games.find({}))
            with open(cache_filepath, 'wb') as cachefile:
                pickle.dump(self.cache, cachefile)

    @pure
    def user_by_username(self, username):
        '''
        Give me a username and I'll give you the player document associated with it, or None if it doesn't exist.
        '''
        matches = filter(lambda p: p['Username'] == username, self.actual_players())
        return None if matches is [] else matches[0]

    @pure
    def actual_players(self):
        '''
        I'm a list of things in the players collection that are actually players.
        '''
        return list(filter(lambda p: 'Username' in p, self.cache['players']))

    @pure
    def users_by_filter(self, user_filter):
        '''
        @param user_filter: any callable (like a function or a lambda) which takes a user document from the database, and returns 'True' if you want me to return it, and 'False' if you don't.
        @return: a list of user docs where the user_filter function/lambda has indicated it should be returned.
        '''
        matches = filter(user_filter, self.actual_players())
        return list(matches)

    @pure
    def completed_games_by_user(self):
        '''
        A dictionary where keys are usernames and values are lists of good completed games by that user.
        '''
        activity = dict()
        for game in filter(lambda g: not game_doc_was_abandoned(g), self.cache['completed_games']):
            if 'usernames' in game.keys():
                activity[game['usernames'][0]] = activity.get(game['usernames'][0], []) + [game]
                activity[game['usernames'][1]] = activity.get(game['usernames'][1], []) + [game]

        return activity

    @pure
    def completed_game_count_by_user(self):
        '''
        The count of completed (good) games, by user.
        '''
        return dict(map(lambda kv_tuple: (kv_tuple[0], len(kv_tuple[1])), self.completed_games_by_user().items()))

    @pure
    def games_user_completed(self, username):
        '''
        The list of games a user successfully completed. If user has completed no games or doesn't exist, returns None.
        '''
        return self.completed_games_by_user().get(username, None)


    @pure
    def number_properly_completed_games(self, username):
        '''
        Give me a username and I'll give you how many completed games they've successfully accomplished.
        '''
        return self.completed_game_count_by_user().get(username, None)


    @pure
    def once_active_users(self, games_limit=1):
        '''
        Returns players who have ever completed more than one game.
        @param games_limit: int limit of games a player has to complete to be included in the returned list
        '''

        activity = self.completed_game_count_by_user()
        useful_active_players = [username for username in activity.keys() if activity[username] > games_limit]

        return self.users_by_filter(lambda p: p['Username'] in useful_active_players)


    @pure
    def ordinary_users(self, include_upper=False, include_lower=False):
        '''
        Returns a list of users who aren't outliers in terms of games played.
        '''
        oau = self.once_active_users()
        oau = sorted(oau, key=lambda p: self.number_properly_completed_games(p['Username']))

        upper_index = len(oau) if include_upper else int(len(oau) * (1-Shepherd.outlier_bound_games_played))
        lower_index = 0 if include_lower else int(len(oau) * Shepherd.outlier_bound_games_played)

        return oau[lower_index:upper_index]

    @pure
    def good_completed_games(self):
        '''
        Returns a list of all completed games that were not abandoned.
        '''
        return list(filter(lambda g: not game_doc_was_abandoned(g), self.cache['completed_games']))
