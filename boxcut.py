import numpy as np
import pandas as pd
from itertools import count
from .boxlist import BoxList
from .boxsort import SortingAlgorithm
from .anneal import Annealer


class BoxCut(SortingAlgorithm):

    def __init__(self, original_matrix):
        super().__init__(original_matrix)
        self.current_matrix = self.orig

    def box_turn(self):
        """
        1. propose move
        2. calculate fitness
        3. calculate probability of accepting move
        (based on fitness differential)
        4. accept move or don't
        """
        # update counters
        self._box_evals += 1
        self._box_t_since_last_move += 1
        candidate = self.propose_box_move(boxes=self.boxes)
        if not candidate:
            return
        # reset parameters
        self._update_if_best(candidate)
        self.best_boxes = self.boxes
        move_accepted = False
        if self.move_is_accepted(cur_fit=self.boxes.fitness,
                                 new_fit=candidate.fitness):
            # why this extra counter? try removing
            # if improvement_ratio != 0:
            #     self._box_t_since_last_move += 1
            self.boxes = candidate
            self._update_if_best(candidate)
            move_accepted = True

        record = (self._box_evals, self._box_t_since_last_move, move_accepted,
                  self.box_temperature, self.boxes.fitness,
                  candidate.fitness, self.best_boxes.fitness, len(self.boxes),
                  len(candidate), len(self.best_boxes))
        return record

    def _probability_to_accept(self, improvement):
        """
        p = 1 when no difference in fitness
        p > 1 when improvement (ie. always accept)
        p gets small very quickly with negative improvement
        """
        return np.exp(improvement / self.box_temperature)

    def move_is_accepted(self, cur_fit, new_fit):
        if new_fit < cur_fit:
            return True
        else:
            improvement = (cur_fit - new_fit) / cur_fit
            p = self._probability_to_accept(improvement)
            return np.random.random() < p

    def propose_box_move(self, boxes):
        # propose move
        candidate = boxes.propose_move()
        if not candidate:
            return
        # calculate fitness
        self._evaluate_box_fitness(candidate, matrix=self.sub_graph)
        return candidate

    def debug(self, matrix):
        it = self._iter_solve(matrix=matrix, debug=True)
        head = list(it.__next__())
        df = pd.DataFrame(list(it), columns=head).set_index('evals')
        return df

    def _update_if_best(self, candidate):
        if candidate < self.best_boxes:
            self.best_boxes = candidate
            self._box_t_since_last_move = 0

    def _initialize_search(self, matrix, boxes=None):
        self.sub_graph = matrix
        self.box_temperature = 0.05
        self._box_t_since_last_move = 0
        self._box_evals = 0  # count turns
        self.boxes = boxes
        if boxes is None:
            self.boxes = BoxList([n + 1 for n in range(len(matrix))])
        self._evaluate_box_fitness(self.boxes, matrix)
        self.best_boxes = self.boxes

    def fit_boxes(self, matrix=None, boxes=None):
        if matrix is None:
            matrix = self.current_matrix
        for i in self._iter_solve(matrix=matrix, boxes=boxes):
            pass
        return self.best_boxes, self.best_boxes.fitness

    def _iter_solve(self, matrix, debug=False, boxes=None):
        self._initialize_search(matrix=matrix, boxes=boxes)
        if debug:
            head = ('evals', 't_since_last_move', 'move_accepted', 'temp',
                    'current_fit', 'new_fit', 'best_fit', 'current_len',
                    'new_len', 'best_len')
            yield head

        n = len(matrix)
        lower_limit = 100
        if n < lower_limit:
            n = lower_limit

        for i in count():
            # every n iterations, lower temp
            if not (i % n):
                self.box_temperature *= 0.9
            # Key Line!
            debug_feed = self.box_turn()
            if self._box_t_since_last_move > n:
                break
            if debug and debug_feed is not None:
                yield debug_feed

    def _evaluate_box_fitness(self, boxes=None, matrix=None):
        """least squares
        sum of squared error from mean within every box
        + the squared error from mean of every cell outside of a box
        """
        if matrix is None:
            matrix = self.current_matrix
        if boxes is None:
            boxes = self.boxes
        boxes.calculate_fitness(matrix)
        # fitness = 0.
        # n = len(matrix)
        # non_box_mask = np.ones(shape=(n, n), dtype=bool)
        # # evaluate the least-squares fitness for each box
        # for begin, end in boxes.items():
        #     # print(begin, end)
        #     non_box_mask[begin:end, begin:end] = False
        #     if end - begin <= 1:
        #         continue
        #     box_nodes = matrix[begin:end, begin:end].copy()
        #     # print(box_nodes)
        #     np.fill_diagonal(box_nodes, np.nan)
        #     # print(box_nodes)
        #     m = np.nanmean(box_nodes)
        #     # print(m)
        #     sq = (box_nodes - m)**2
        #     fitness += np.nansum(sq)
        #     # print(fitness)
        # if non_box_mask.any():
        #     # now do it for the non-box nodes
        #     non_box_nodes = matrix[non_box_mask]
        #     # print(non_box_nodes)
        #     m = non_box_nodes.mean()
        #     sq = (non_box_nodes - m)**2
        #     fitness += sq.sum()
        # # print(fitness)
        # boxes.fitness = fitness


class BoxCut2(Annealer):

    def __init__(self, original_matrix):
        self.matrix_size = len(original_matrix)
        self.orig = original_matrix
        self.current_matrix = self.orig
        # build a weight matrix that falls away from the diagonal this will be
        # useful later when
        self.weight_matrix = np.ones(self.orig.shape)
        for i in range(self.matrix_size):
            for j in range(self.matrix_size):
                self.weight_matrix[i, j] -= (abs(i - j) /
                                             float(self.matrix_size))

    def propose_move(self):
        # propose move
        pass

    def evaluate_fitness(self, candidate):
        candidate.calculate_fitness()


    def _initialize_state(self, matrix, boxes=None):
        self.sub_graph = matrix
        self.box_temperature = 0.05
        self._box_t_since_last_move = 0
        self._box_evals = 0  # count turns
        self.boxes = boxes
        if boxes is None:
            self.boxes = BoxList([n + 1 for n in range(len(matrix))])
        self._evaluate_box_fitness(self.boxes, matrix)
        self.best_boxes = self.boxes
