import sys, copy, heapq

import math, random
import numpy as np

################################################################################
#
################################################################################

class KanbanBoard():

    def __init__(self,clone):
        if clone is not None:
            self._predict,  = copy.copy(clone._predict)
            self._memento = clone._memento
        else :
            self._predict, self._memento = None, None
            pass

    def predict(self):
        return self._predict[0]

    def update(self,state):
        self._predict.pop(0)

    @property
    def memento(self):
        if self._memento is None:   return self
        pass
        self._predict = copy.copy(self._memento._predict)

    @memento.setter
    def memento(self,setter):
        pass
        self._memento._predict = copy.copy(setter._predict)

    def correction(self,state):
        pass

################################################################################
#
################################################################################

class AgentBoard():

    def __init__(self,clone):
        if clone is not None:
            self.nb_ingred,self.nb_match,self.price = clone.nb_ingred,clone.nb_match,clone.price
            self.action = clone.action
        else :
            self.nb_ingred,self.nb_match,self.price = 0, 0, 0
            self.action = []

        self._predict = copy.copy(clone._predict) if clone is not None else []
        self._memento = clone._memento if clone is not None else self

    def setup(self,state):
        for k1, k2 in zip( f_ingred(self.action) , state):
            pass

    def compute(self,spell):
        pass

    def predict(self):
        return next(iter(self._predict))

    def update(self,state):
        pass

    @property
    def memento(self):
        if self._memento is None:   return self

        pass

        self._predict = copy.copy(self._memento._predict)
        return self

    @memento.setter
    def memento(self,setter):
        self._memento = self.action[:]

        self._memento._predict = copy.copy(setter._predict)


    def correction(self,state):
        pass

################################################################################
#
################################################################################

class KanbanSimu():

    def __init__(self,clone):
        if clone is not None:
            pass
        else :
            pass
        self._predict = copy.copy(clone._predict)
        self._memento = clone._memento

    def predict(self):
        return next(iter(self._predict))

    @update.setter
    def update(self,state):
        pass

    @property
    def memento(self):
        if self._memento is None:   return self
        pass
        self._predict = copy.copy(self._memento._predict)

    @memento.setter
    def memento(self,setter):
        pass
        self._memento._predict = copy.copy(setter._predict)


    def correction(self,state):
        pass

################################################################################
#
################################################################################

class AgentSimu():

    def __init__(self,clone):
        if clone is not None:
            pass
        else :
            pass
        self._predict = copy.copy(clone._predict)
        self._memento = clone._memento

    def predict(self):
        return next(iter(self._predict))

    @update.setter
    def update(self,state):
        pass

    @property
    def memento(self):
        if self._memento is None:   return self
        pass
        self._predict = copy.copy(self._memento._predict)

    @memento.setter
    def memento(self,setter):
        pass
        self._memento._predict = copy.copy(setter._predict)


    def correction(self,state):
        pass

################################################################################
#
################################################################################

if __name__ == '__main__':

    _mine_ = KanbanBoard(None)
    _opp_ = KanbanBoard(None)
    _simu_ = KanbanSimu(None)

    _mine_agent_ = {}
    _opp_agent_ = {}
    _simu_agent_ = {}

    while True:
        #   READ
