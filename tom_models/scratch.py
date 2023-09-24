from dataclasses import dataclass
import birch_curve_calculation_utilities as curveutils


@dataclass
class ModelParameters:
    c: float
    curve_inflection_relative_to_numgames: float
    prob_bored: float
    boredom_enabled: bool
    training_data: list
    testing_data: list
    assumed_confidence_plateau: float
    starting_confidence: float
    iteration_base: int
    number_simulated_players: int
    advice: list[tuple[str, str, str|callable]]
    players:list[str]
    args:list[any]
    kwargs:dict[str:any]
        
    def __repr__(self) -> str:
        return f"params for {', '.join(self.players)}:c={self.c}, prob bored={self.prob_bored}, boredom {'en' if self.boredom_enabled else 'dis'}abled, confidence model assumes low of {self.starting_confidence}, high of {self.assumed_confidence_plateau}, iteration base={self.iteration_base}, #simulated players={self.number_simulated_players}, rgr inflection relative to #games={self.curve_inflection_relative_to_numgames}, #training games={len(self.training_data)}, #testing games={len(self.testing_data)}"

    def __getstate__(self) -> object:
        state = self.__dict__.copy()
        pickleable_advice = list()
        for type, join_point, aspect in state['advice']:
            pickleable_advice.append((type, join_point, aspect.__name__))
        state['advice'] = pickleable_advice
        return state

    def __setstate__(self, d):
        self.__dict__ = d
        unpickled_advice = list()
        for type, join_point, aspect in d['advice']:
            unpickled_advice.append((type, join_point, eval(aspect)))
        self.advice = unpickled_advice
        if 'args' not in d:
            self.args = list()
        if 'kwargs' not in d:
            self.kwargs = dict()

    @property
    def boredom_period(self) -> int:
        '''
        Number of games to play before checking player boredom.
        Attempts to allow every player combo to play each other once on average before checking again.
        '''
        return int(self.number_simulated_players**2)/2

    def active_dataset(self, testing) -> list:
        return self.testing_data if testing else self.training_data

    def iterations(self, testing) -> int:
        if self.boredom_enabled:
            return self.iteration_base
        
        return int(self.number_simulated_players**2 * len(self.active_dataset(testing)) / 2)

    def rgr(self, testing) -> float:
        '''
        RGR for this C value, number of games to play, and start/end confidences.
        '''
        if not hasattr(self, '_rgr_cache'):
            self._rgr_cache = dict()
        if self._rgr_cache.get(testing) is None:
            num_games_to_confidence = len(self.active_dataset(testing)) * self.curve_inflection_relative_to_numgames
            self._rgr_cache[testing] = \
                curveutils.rgr_yielding_num_games_for_c(
                    num_games_to_confidence,
                    self.c,
                    start=self.starting_confidence,
                    limit=self.assumed_confidence_plateau)
        return self._rgr_cache[testing]
        
    def run_experiment(self, testing, correlation_metric):
        real, synthetic = compare_with_multiple_players(rgr_control=self.rgr(testing=False),
                                                                    iterations=self.iterations(testing=False),
                                                                    games=self.training_data,
                                                                    players=self.players,
                                                                    birch_c=self.c,
                                                                    sigmoid_initial_confidence=self.starting_confidence,
                                                                    boredom_confidence=self.assumed_confidence_plateau,
                                                                    num_synthetic_players=self.number_simulated_players,
                                                                    boredom_period=self.boredom_period,
                                                                    prob_bored=self.prob_bored,
                                                                    advice=self.advice,
                                                                    *self.args,
                                                                    **self.kwargs)
        return Result(self, real, synthetic, correlation_metric, testing)
        
        
