from typing import Generator
from cachetools import Cache
from .definition import AlgorithmHeuristic, Algorithm
from game_state_divercite import GameStateDivercite
import numpy as np
from .constant import *
from gc import collect
from random import random


class MinimaxTypeASearch(Algorithm):

    def __init__(self, typeA_heuristic: AlgorithmHeuristic, max_depth: int | None, cache: Cache, allowed_time: float = None):
        super().__init__(typeA_heuristic, cache, allowed_time)
        self.max_depth = max_depth
        self.hit = 0
        self.node_expanded = 0

    def _search(self):
        _, action_star = self._minimax(self.current_state, True, float(
            '-inf'), float('inf'), 0, self.max_depth)
        return action_star

    def __del__(self):
        ...

    def _minimax(self, state: GameStateDivercite, isMaximize: bool, alpha: float, beta: float, depth: int, max_depth: int = None):
        if state.is_done():
            return self._utility(state), None

        if depth >= max_depth:
            pred_utility: float = self.main_heuristic(
                state, my_id=self.my_id, opponent_id=self.opponent_id, my_pieces=self.my_pieces, opponent_pieces=self.opponent_pieces,
                last_move=self.last_move, is_first_to_play=self.is_first_to_play, moves=self.moves,
                my_score=self.my_score, opponent_score=self.opponent_score)
            if self._isQuiescent(state, pred_utility):
                return pred_utility, None

        v_star = float('-inf') if isMaximize else float('inf')
        m_star = None

        for action in self._compute_actions(state):
            new_state = self._transition(state, action)
            next_max_depth = self._compute_next_max_depth(
                max_depth, state.step, depth, action)

            #  NOTE put it in a separate method
            if self.cache != None:
                hash_state = self._hash_state(new_state.rep.env)
                if hash_state not in self.cache:
                    flag, _hash = self.check_symmetric_moves_in_cache(
                        new_state.rep.env)
                    if flag:
                        hash_state = _hash
                    else:
                        self.cache[hash_state] = self._minimax(
                            new_state, (not isMaximize), alpha, beta, depth+1, next_max_depth)

                v, _ = self.cache[hash_state]
            else:
                v, _ = self._minimax(
                    new_state, (not isMaximize), alpha, beta, depth+1, next_max_depth)

            flag = (v > v_star) if isMaximize else (v < v_star)
            if flag:
                v_star = v
                m_star = action[0] if isinstance(
                    action, (list, tuple)) else action

            if isMaximize:
                alpha = max(alpha, v_star)
            else:
                beta = min(beta, v_star)

            if v_star >= beta and isMaximize:
                return v_star, m_star
            if v_star <= alpha and not isMaximize:
                return v_star, m_star

        return v_star, m_star

    def _isQuiescent(self, state: GameStateDivercite, pred_utility: float) -> bool:
        # TODO
        return True

    def _compute_next_max_depth(self, current_max_depth: int, *args) -> int:
        return current_max_depth

    def _filter_action(self, states: GameStateDivercite) -> Generator:
        return states.generate_possible_light_actions()

    def _compute_actions(self, state: GameStateDivercite):
        return self._filter_action(state)

    def _clear_cache(self):
        if (MAX_STEP - self.current_state.step) <= self.max_depth:
            print('Not clearing the cache cause we already compute it')
            super()._clear_cache()


class MinimaxHybridSearch(MinimaxTypeASearch):

    MAX_THRESHOLD = 0

    def __init__(self, cache: Cache, typeB_heuristic: AlgorithmHeuristic, allowed_time: float = None, typeA_heuristic: AlgorithmHeuristic = None, threshold: float = 0.5, n_expanded: int | None = None, max_depth: int = MAX_STEP):
        super().__init__(typeA_heuristic, max_depth, cache, allowed_time)
        self.n_max_expanded = n_expanded
        self.typeB_heuristic = typeB_heuristic
        if threshold < self.MAX_THRESHOLD:
            threshold = self.MAX_THRESHOLD
        self.threshold = threshold
        if typeA_heuristic is None:
            self.main_heuristic = typeB_heuristic

    def _order_actions(self, actions: Generator | list, current_state: GameStateDivercite) -> list[tuple]:
        def _apply(a):
            return self.typeB_heuristic(current_state.apply_action(a[0]), my_id=self.my_id, opponent_id=self.opponent_id,
                                        my_pieces=self.my_pieces, opponent_pieces=self.opponent_pieces,
                                        last_move=self.last_move, is_first_to_play=self.is_first_to_play, moves=self.moves,
                                        my_score=self.my_score, opponent_score=self.opponent_score)

        returned_actions = np.fromiter(actions, dtype=np.object_)
        vals = np.apply_along_axis(
            _apply, axis=0, arr=returned_actions.reshape(1, -1))
        n_child = len(returned_actions)
        max_child_expanded = self._compute_n_expanded(
            current_state.step, n_child)
        vals_indice = vals.argsort(axis=0)[::-1][:max_child_expanded]

        return zip(returned_actions[vals_indice], vals[vals_indice])

    def _compute_actions(self, state: GameStateDivercite):
        actions = self._filter_action(state)
        return self._order_actions(actions, state)

    def _filter_action(self, states):
        # TODO
        return super()._filter_action(states)

    def _isQuiescent(self, state, pred_utility):
        # TODO If the step is less than the last step, we should check if the moves is safe
        return True

    def _transition(self, state, action):
        return super()._transition(state, action[0])

    def _compute_next_max_depth(self, current_max_depth: int, current_step: int, current_depth, action: tuple,):
        # ERROR most of the value are negative
        _eval: float = action[1]
        if _eval >= self.threshold:
            return self.max_depth

        if _eval < self.MAX_THRESHOLD:
            print(_eval)
            return current_depth

        if random() < self._proba_by_temperature(_eval, current_step):
            return current_max_depth - current_depth

        return current_depth

    def _proba_by_temperature(self, _eval, current_step):
        return _eval*2 * ((MAX_STEP-current_step+C_TEMP_NUM)/C_TEMP_DEN)

    def _compute_n_expanded(self, cur_step: int, n_child: int):
        # TODO dynamically update the number of nodes expanded
        return self.n_max_expanded if self.n_max_expanded != None and self.n_max_expanded < n_child else n_child


class IterativeDeepeningSearch(Algorithm):
    ...
