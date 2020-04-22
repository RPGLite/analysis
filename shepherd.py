from pymongo import MongoClient
import datetime
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


class ShepherdConfig:
    def __init__(self):
        # Flags to filter out useful things
        self.remove_developers = True
        self.remove_beta_testers = False
        self.include_only_active_users = True

        # Functions that take a game / user and return the thing to sort on. For example, sorting by skill points below.
        self.user_sort_by = lambda user: user['skill_points']
        self.game_sort_by = lambda game: game.get('end_time', datetime.datetime.now())

        # Add functions to these lists, and we'll filter games and users using them.
        # To be clear: add a function that takes a game / user and returns True if you want to keep it and False if you don't. You can add as many as you want.
        self.user_filters = list()
        self.game_filters = list()

        # Useful lists for filtering folk out who might affect results.
        self.developers = ['probablytom', 'cptKav']
        self.beta_testers = ['Ellen', 'Fbomb', 'demander', 'Marta', 'creilly2', 'georgedo', 'apropos0']  # TODO: Tons more to add here

        # Should we filter games to only include users we would keep?
        # i.e. if you set remove_developers to be True, then any game involving developers will be discarded.
        self.filter_games_by_users = True



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
        while not len(return_cache.keys()) == 0:
            del return_cache[list(return_cache.keys())[0]]

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

    def __init__(self, load_cache_by_file=False, config=None):
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


        self.config = config if config is not None else ShepherdConfig()

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

    def reset_config(self, new_config):
        clear_pure_cache()
        self.config = new_config

    @pure
    def user_by_username(self, username):
        '''
        Give me a username and I'll give you the player document associated with it, or None if it doesn't exist.
        '''
        matches = list(filter(lambda p: p['Username'] == username, self.actual_players()))
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
    def filtered_users(self, include_upper=False, include_lower=False):
        '''
        Returns a list of users filtered by the Shepherd configuration.
        '''

        # This is the set of users that we'll filter down over time. Begins as all user documents.
        current_user_set = self.actual_players()

        # First, if we've been told to get active users, then filter inactive users out.
        if self.config.include_only_active_users:
            # Active players can be detected from the games they have completed.
            active_player_usernames = self.completed_game_count_by_user().keys()
            active_players = filter(lambda player: player['Username'] in active_player_usernames,
                                         current_user_set)
            current_user_set = active_players

        # If we've been told to filter out developers, do that now.
        if self.config.remove_developers:
            current_user_set = filter(lambda player: player['Username'] not in self.config.developers,
                                           current_user_set)

        # Remove beta testers if we don't want to see them either
        if self.config.remove_beta_testers:
            current_user_set = filter(lambda player: player['Username'] not in self.config.beta_testers,
                                           current_user_set)

        # If there are any user filtering functions in the config, apply them now.
        for config_filter in self.config.user_filters:
            current_user_set = filter(config_filter, current_user_set)


        # Sort by any sorting metric we've been given. This defaults to sorting by skill points.
        current_user_set = sorted(current_user_set, key=self.config.user_sort_by)


        return list(current_user_set)

    @pure
    def filtered_games(self):

        current_game_set = self.all_non_abandoned_games()

        if self.config.filter_games_by_users:

            valid_users_by_username = list(map(lambda user: user['Username'],
                                               self.filtered_users()))

            def player_1_valid(game):
                return game['usernames'][0] in valid_users_by_username

            def player_2_valid(game):
                return game['usernames'][1] in valid_users_by_username

            current_game_set = filter(lambda game: player_1_valid(game) and player_2_valid(game),
                                      current_game_set)

        for game_filter in self.config.game_filters:
            current_game_set = filter(game_filter, current_game_set)

        current_game_set = sorted(current_game_set, key=self.config.game_sort_by)
        return list(current_game_set)

    @pure
    def all_non_abandoned_games(self):
        '''
        Returns a list of all completed games that were not abandoned.
        '''
        return list(filter(lambda g: not game_doc_was_abandoned(g), self.cache['completed_games']))
