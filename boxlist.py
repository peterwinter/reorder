from collections import abc
import random
import numpy as np


class BaseBoxList(abc.MutableSequence):
    """ basic class functionality """
    # def __init__(self, boxes=[]):
    #     self.boxes = boxes
    #     self.fitness = None

    # def copy(self):
    #     return self.__class__(boxes=self.boxes.copy())

    # TODO: look into why the above functions work slightly better
    def __init__(self, boxes=[], fitness=np.inf):
        self.boxes = boxes
        self.fitness = fitness

    def copy(self):
        return self.__class__(boxes=self.boxes.copy(), fitness=self.fitness)

    def __getitem__(self, key):
        return self.boxes[key]

    def __setitem__(self, key, value):
        self.boxes[key] = value

    def __delitem__(self, key):
        del self.boxes[key]

    def __len__(self):
        return len(self.boxes)

    def __repr__(self):
        f = round(self.fitness, ndigits=2)
        return 'Fit:{f} Boxes: {b}'.format(f=f, b=self.boxes)

    def insert(self, key, value):
        self.boxes.insert(key, value)

    def __lt__(self, other):
        return self.fitness < other.fitness

    def __le__(self, other):
        return self.fitness <= other.fitness

    def __eq__(self, other):
        return self.fitness == other.fitness

    def __ne__(self, other):
        return self.fitness != other.fitness

    def __gt__(self, other):
        return self.fitness > other.fitness

    def __ge__(self, other):
        return self.fitness >= other.fitness

    def items(self):
        boxes = self.boxes
        yield 0, boxes[0]
        for begin, end in zip(boxes, boxes[1:]):
            yield begin, end

class BoxList(BaseBoxList):

    # def __init__(self, boxes=[]): #, fitness=np.inf):
    #     super().__init__(boxes=boxes)#, fitness=fitness)


    def _random_bounded_pareto(self, limit):
        d = np.inf
        while d > limit:
            d = int(np.ceil((np.random.pareto(0.5))))
        return d

    def _determine_takeover_size(self, limit):
        takeover_size = 1
        if limit > 1:
            takeover_size = self._random_bounded_pareto(limit=limit)
        return takeover_size

    def right_join(self, box_pos):
        """
        take some items from box on right.

        amount of items taken is _random_bounded_pareto()

        None is returned if no box to right.
        (ie. box_pos at limit)
        """
        # join with the one to the right
        candidate = self.copy()
        if box_pos == len(self.boxes) - 1:
            return

        current_edge = candidate[box_pos]
        upper_bound = candidate[box_pos + 1]

        takeover_limit = (upper_bound - current_edge)
        takeover_size = self._determine_takeover_size(limit=takeover_limit)

        new_edge = current_edge + takeover_size
        # if cut_location is the next box, remove current box
        if new_edge == upper_bound:
            candidate.pop(box_pos)
        # if cut location is smaller than next box, move to next spot
        else:
            candidate[box_pos] = new_edge
        return candidate

    def left_join(self, box_pos):
        """
        take some items from box on left.

        amount of items taken is _random_bounded_pareto()
        this moves the index of the box at box_pos - 1.

        None is returned if no box to left.
        (ie. box_pos = 0)
        """
        candidate = self.copy()

        if box_pos == 0:
            return

        lower_bound = 0  # seems like it should be one?
        if box_pos > 1:
            lower_bound = candidate[box_pos - 2]
        current_edge = candidate[box_pos - 1]

        takeover_limit = current_edge - lower_bound
        takeover_size = self._determine_takeover_size(limit=takeover_limit)

        new_edge = current_edge - takeover_size
        if new_edge == lower_bound:
            candidate.pop(box_pos - 1)
        else:
            candidate[box_pos - 1] = new_edge
        return candidate

    def split(self, box_pos):
        """ return a split list or None if box_pos doesn't work

        new item gets inserted at box_pos and existing item
        is shifted right.

        ie. new item inserted left of existing item

        all box_pos are possible
        limitations, if the box in a given position is too small... no luck
        """
        candidate = self.copy()
        upper = candidate[box_pos]
        lower = 1
        if box_pos > 0:
            lower = candidate[box_pos - 1]
        r = upper - lower
        if r <= 1:
            return
        cut_location = random.randrange(lower + 1, upper)
        candidate.insert(box_pos, cut_location)
        return candidate

    def propose_move(self):
        """
        1. pick a random position in box list
        2. randomly pick if doing a split or join on position
        """
        candidate = self.copy()
        # split
        if random.random() < 0.5:
            box_pos = random.randrange(len(self.boxes))
            candidate = candidate.split(box_pos)
        # join
        else:
            if random.random() < 0.5:
                # join with the one to the left
                box_pos = random.randrange(len(self.boxes) - 1)
                candidate = candidate.right_join(box_pos)
            else:
                # join with the one to the right
                box_pos = random.randrange(1, len(self.boxes))
                candidate = candidate.left_join(box_pos)
        return candidate