from Divercite.lib._strategy import Algorithm
from .constant import *

class AlgoController:
    
    def __init__(self):
        self.strategy:list[Algorithm] = []
        self.strategy_count = 0

    def __call__(self, *args, **kwds):
        return self.play_best(*args)

    def play_best(self, moves_index:int):
        algorithm = self[moves_index]
        return algorithm.search()
        
    def add_strategy(self, moves_index:int,algorithm:Algorithm):
        if moves_index < len(self.strategy):
            raise IndexError
            
        if moves_index > MAX_MOVES:
            moves_index = MAX_MOVES - moves_index

        self.strategy.extend([algorithm for _  in range(moves_index)])
        return self
        
    def __getitem__(self,move_index) -> Algorithm:
        return self.strategy[move_index]
    
    def strategy_from_dict(self, strategy:dict[int,Algorithm],clear=False):
        if clear:
            self.strategy.clear()

        for move_step,algo in strategy.items():
            self.add_strategy(move_step,algo)

_algoController = AlgoController()

