import sys, copy, math, random, time, heapq

TURN = 0
LEARNED = 0
TYPE_SET = { 'CAST' : 0 , 'OPPONENT_CAST' : 1 , 'LEARN' : 2 , 'BREW' : 3 }
TYPE_CAST, TYPE_OPP_CAST, TYPE_LEARN, TYPE_BREW = 0 , 1 , 2 , 3

FUZZY_GET = {
    -5:0, -4:0, -3:0, -2:0 , -1: 0,
    0: 0,
    1: 1, 2: 1,
    3:2 , 4:2 , 5:2 ,
    6:3 , 7:3 , 8:3 , 9:3 ,
    10: 3, 11:3, 12:3, 13:3
}
FUZZY_MIN = ( 0 , 1 , 3 , 6 )
FUZZY_MAX = ( 0 , 2 , 5 , 9 )
FUZZY_STATE = len(FUZZY_MIN) ** 4

FUZZY_QUANTITY = {
    -6: 300, -5: 300, -4: 300, -3: 300, -2: 300, -1: 300,
    0: 0,
    1: 100, 2: 100,
    3: 200, 4: 200, 5: 200, 6: 200
}

_action_board_ = {}
_learn_board_ = []

_mine_board_ = []
_opp_board_ = []

_mine_agent_ = {}
_opp_agent_ = {}

f_id = lambda obj : obj[0]
f_type = lambda obj : obj[1]
f_ingred = lambda obj : obj[2:6]
f_gain = lambda obj : 1 * obj[2] + 2 * obj[3] + 3 * obj[4] + 4 * obj[5]
f_price = lambda obj : obj[6]
f_tome = lambda obj : obj[7]
f_tax = lambda obj : obj[8]
f_cast = lambda obj : obj[9]
f_repeat = lambda obj : obj[10]

f_state = lambda obj : obj[0:4]
f_quantity = lambda obj : sum(obj[0:4])
f_quality = lambda obj :  13 * (10 - sum(obj[0:4])) + 11 * obj[0] + 7 * obj[1] + 5 * obj[2] + 3 * obj[3]
f_score = lambda obj : obj[4]

def inv_findBrew( state1 , state2 ):
    _ = 0
    for k1, k2 in zip(state1,state2) :
        _ = _ + max( (-k2) - k1 , 0)
    return _

def inv_int2inv( i1 ) :
    _ = [ (i1) % 4 , (i1 >> 2) % 4 , (i1 >> 4) % 4 , (i1 >> 6) % 4 ]
    return _

def inv_inv2int( s1 ) :
    _ = sum([ i1 * (1 << i2) for i1,i2 in zip(s1,[0,2,4,6]) ])
    return _

k_map = {}

class LearnNeuron():

    def __init__(self,param):
        self.param = param

    def spell(self,state):
        _ = state[:]
        _[0] = state[0] - f_tome(self.param)
        if _[0] >= 0 :
            _[0] = _[0] + f_tax(self.param)
        return _

    def gain(self):
        return min( (f_tax(self.param) - f_tome(self.param)) , 4 )

    def __str__(self):
        return f'(learn:{f_id(self.param)})'

    def read(self):
        return f'LEARN {f_id(self.param)}'

class SpellNeuron():

    def __init__(self,param):
        self.param = param

    def spell(self,state):
        _ = state[:]
        for i in range(4):  _[i] = state[i] + f_ingred(self.param)[i]
        return _

    def gain(self):
        return 1 * self.param[2] + 2 * self.param[3] + 3 * self.param[4] + 4 * self.param[5]

    def __str__(self):
        return f'({f_id(self.param)})'

    def read(self):
        return f'CAST {f_id(self.param)}'

class RestNeuron():

    def __init__(self,param):
        self.param = None

    def __str__(self):
        return f'rest'

    def read(self):
        return f'REST'

class BrewNeuron():

    def __init__(self,param):
        self.param = param

    def spell(self,state):
        _ = state[:]
        for i in range(4):  _[i] = state[i] + f_ingred(self.param)[i]
        return _

    def gain(self):
        return f_price(self.param)

    def __str__(self):
        return f'(brew:{f_id(self.param)})'

    def read(self):
        return f'BREW {f_id(self.param)}'

################################################################################
#
################################################################################

class KanbanBoard():

    def __init__(self,clone):
        self.observer = []
        self.cast, self.state, self.learn = set(), [], []
        self.spell = [ [] for i1 in range(FUZZY_STATE) ]
        self.learned = []
        self.tolearnpositive = [ None ] * 4
        #self.tolearnpositive[0] = 1
        self.tolearnnegative = [ None ] * 4
        self.tolearnnegative[3] = 1
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

        self.state = self._memento.state[:]
        self.spell = self._memento.spell[:]
        self.cast = copy.copy(self._memento.cast)
        pass
        self._predict = copy.copy(self._memento._predict)

    @memento.setter
    def memento(self,setter):
        self._memento.state = setter.state[:]
        self._memento.spell = setter.spell[:]
        self._memento.cast = copy.copy(setter.cast)
        pass
        self._memento._predict = copy.copy(setter._predict)

    def correction(self,state):
        pass

    def compute_4(self):
        _learn_id_, _learn_k1_ = -1,-1

        for i2 , _ in zip([0,1,2,3,4,5], self.learn[ 0 : min(self.state[0] + 1, 2) ]):

            if f_gain(_.param) > 0 :

                for i1, l1, l2 in zip([2,3,4,5],self.tolearnpositive,self.tolearnnegative) :

                    if l1 is None and f_repeat(_.param) == 1 and 4 > _.param[i1] > 0:
                        self.tolearnpositive[i1 - 2] = _
                        _learn_id_ = f_id(_.param)
                        _learn_k1_ = i2
                    if l2 is None and f_repeat(_.param) == 1 and -3 < _.param[i1] < 0:
                        self.tolearnnegative[i1 - 2] = _
                        _learn_id_ = f_id(_.param)
                        _learn_k1_ = i2

                if _learn_id_ != -1:
                    return ( _learn_id_ , _learn_k1_ )

        return ( -1 , -1 )

    def compute_3(self):
        s1 = self.state[:]
        t1 = self.spell[:]

        p1 = []
        #d1 = len(p1) + f_quality(s1)
        c1 = copy.copy(self.cast)
        d1 = f_quality(s1) + len(c1)

        resolve = []
        already = set()
        search_turn = 1

        already_add = already.add
        already_remove = already.remove
        heapq_heappush = heapq.heappush
        heapq_heappop = heapq.heappop

        already_add( ( 1 , d1 ) )
        heapq.heappush( resolve , ( 1 , d1 , s1 , t1 , c1 , p1 ) )

        soluce = []

        while len(resolve) > 0 and search_turn < 325 :
            search_turn = search_turn + 1

            g1 , d1 , s1 , t1 , c1 , p1 = heapq_heappop(resolve)

            already_remove( (g1,d1) )

            delete = []
            for update in self.observer:
                if update.check_2( self , g1 , s1 , p1 ) is not None :
                    delete.append( update )

            for update in delete :
                self.detach_compute(update)

            if len(self.observer) == 0 :
                break

            if g1 > 30 :    break

            i1 = inv_inv2int( [ FUZZY_GET[i1] for i1 in f_state(s1) ] )

            a1 = t1[i1]
            if g1 == 1 :
                a1 = self.learn[ 0 : s1[0] + 1 ] + t1[i1]

            for _ in a1 :

                next_g1, next_d1, next_s1, next_t1, next_c1, next_p1 = g1, d1, s1, t1, c1, p1

                _in_repeat_ = False

                while _ in a1:

                    next_s1 = _.spell(next_s1)

                    next_p1 = next_p1[:]
                    next_p1.append( _ )

                    if _in_repeat_ == True :

                        next_g1 = next_g1 - _.gain()

                        next_d1 = f_quality(next_s1) + len(next_c1)

                    else :

                        next_g1 = next_g1 + (5 - _.gain() )
                        next_c1 = copy.copy(next_c1)

                        if _ in next_c1 :
                            next_g1 = next_g1 + 5
                            next_c1 = set()
                        elif f_type(_.param) == 2 :
                            pass
                        else:
                            next_c1.add(_)

                        next_d1 = f_quality(next_s1) + len(next_c1)

                    if (next_g1,next_d1) not in already and sum(next_s1[0:4]) <= 10 :

                        next_t1 = next_t1
                        if f_type(_.param) == 2 :
                            next_t1 = self.setup_7( _ , next_t1 )

                        already_add( (next_g1, next_d1) )
                        heapq_heappush( resolve , ( next_g1 , next_d1 , next_s1 , next_t1 , next_c1 , next_p1 ) )

                    if f_type(_.param) != 2 and f_repeat(_.param) == 1 :

                        i1 = inv_inv2int( [ FUZZY_GET[i1] for i1 in f_state(next_s1) ] )

                        a1 = next_t1[i1]

                        _in_repeat_ = True

                    else:
                        break


    def setup_4(self,state):
        self.state = state[:]

    def setup_6(self, learn):
        self.learn = learn[:]

    def setup_5(self,spell):
        self.spell = []
        for i1 in range(FUZZY_STATE):
            self.spell.append( [] )
            s1 = inv_int2inv(i1)

            for _ in spell.values():

                min1 = [ FUZZY_MIN[i1] for i1 in s1 ]
                max1 = [ FUZZY_MAX[i1] for i1 in s1 ]

                min1 = _.spell( min1 )
                min1 = sum([1 for i1 in min1 if i1 < 0 ])

                max2 = _.spell( max1 )
                max2 = sum(max2)

                if min1 == 0 and max2 <= 10:
                    self.spell[i1].append(_)

    def setup_8(self,spell):
        if spell in self.learned :
            return
        else :
            self.learned.append(spell)

        for i1 in range(FUZZY_STATE):
            s1 = inv_int2inv(i1)

            _ = spell

            min1 = [ FUZZY_MIN[i1] for i1 in s1 ]
            max1 = [ FUZZY_MAX[i1] for i1 in s1 ]

            min1 = _.spell( min1 )
            min1 = sum([1 for i1 in min1 if i1 < 0 ])

            max2 = _.spell( max1 )
            max2 = sum(max2)

            if min1 == 0 and max2 <= 10:
                self.spell[i1].append(_)

    def setup_7( self , spell , tome ):
        next_t1 = [ [] ] * FUZZY_STATE
        _ = list(spell.param)
        _[1] = 0 # Warning not okay in case opponent
        _ = SpellNeuron( tuple(_))
        for i1, t1 in zip( range(FUZZY_STATE) , tome):
            s1 = inv_int2inv(i1)

            min1 = [ FUZZY_MIN[i1] for i1 in s1 ]
            max1 = [ FUZZY_MAX[i1] for i1 in s1 ]

            min1 = _.spell( min1 )
            min1 = sum([1 for i1 in min1 if i1 < 0 ])

            max2 = _.spell( max1 )
            max2 = sum(max2)

            next_t1[ i1 ] = t1 [:]
            if min1 == 0 and max2 <= 10:
                next_t1[i1].append(_)

        return next_t1


    def attach_compute(self,instance):
        self.observer.append(instance)

    def detach_compute(self,instance):
        if instance in self.observer:
            self.observer.remove(instance)

################################################################################
#
################################################################################

class AgentBoard():

    def __init__(self,clone):
        if clone is not None:
            self.nb_ingred,self.nb_match,self.price = clone.nb_ingred,clone.nb_match,clone.price
            self.state, self.cast = clone.state, clone.cast
            self.action, self.down, self.spell = clone.action, clone.down, clone.spell
            self.k = clone.k
        else :
            self.nb_ingred,self.nb_match,self.price = 0, 0, 0
            self.state, self.cast = [], set()
            self.action, self.down, self.spell = None, None, []
            self.k = 999

        self._predict = copy.copy(clone._predict) if clone is not None else []
        self._memento = clone._memento if clone is not None else self

    def compute_2(self):
        d1 = set()
        _ = []

        for p1 in self._predict:
            if p1 not in d1:
                _.append(p1)
                d1.add(p1)
            else:
                _.append( RestNeuron(None) )
                _.append(p1)
                d1 = set()
                d1.add(p1)

        _.append( self.action )

        self._predict = _

    def check_2( self , caller , gain , state , predict ):
        soluce = []
        if inv_findBrew( f_state(state) , f_ingred(self.action.param) ) == 0 :
            soluce = predict[:]
            soluce.append( self.action )
            pass

        else :
            return None

        self.k = max(gain,1)
        self._predict = soluce
        return self

    def reset_predict(self):
        self._predict = []
        self.k = 999

    def predict(self):
        return self._predict[0]

    def update(self,state):
        self._predict.pop(0)

    @property
    def memento(self):
        if self._memento is None:   return self

        pass

        self._predict = copy.copy(self._memento._predict)
        return self

    @memento.setter
    def memento(self,setter):
        self._memento.down = setter.down
        self._memento.spell = setter.spell
        self._memento.action = setter.action
        self._memento.state = setter.state[:]
        self._memento.cast = copy.copy(setter.cast)

        self._memento = copy.copy(setter)
        self._memento._predict = copy.copy(setter._predict)

    def correction(self,state):
        pass

k_2know = [ 2 , 3 , 4 , 12 , 13 , 14 , 15 , 16 ]

if __name__ == '__main__':

    _min_id_ = -1
    _min_len_ = math.inf

    _learn_id_ = TURN
    _learn_set_ = { 0 : -1 , 1 : -1 , 2 : -1 , 3 : -1 , 4 : -1 }

    _mine_ = KanbanBoard(None)

    while True:
        TURN = TURN + 1
        out = ''

        no_delete = []
        _learn_board_ = []
        for i in range( int(input()) ):
            _ = input().split()

            _[0], _[1], _[2:] = int(_[0]), TYPE_SET[_[1]], map(int,_[2:])

            if f_type(_) == TYPE_CAST :
                if f_id(_) not in _mine_agent_:
                    _mine_agent_[ f_id(_) ] =  SpellNeuron( tuple(_) )
                    _min_id_ = -1
                    _min_len_ = math.inf
                    for _ in _action_board_.values(): _._predict = []

            elif f_type(_) == TYPE_OPP_CAST :
                if f_id(_) not in _opp_agent_:
                    _opp_agent_[ f_id(_) ] = SpellNeuron( tuple(_) )

            elif f_type(_) == TYPE_LEARN :
                _learn_board_.append( LearnNeuron( tuple(_) ) )

            elif f_type(_) == TYPE_BREW and _[0] in _action_board_ :
                no_delete.append( _[0] )

            elif f_type(_) == TYPE_BREW :
                no_delete.append( _[0] )
                _action_board_ [ _[0] ] = AgentBoard(None)
                _action_board_[ _[0] ].action = BrewNeuron( tuple(_) )

        delete = [ _ for _ in _action_board_.keys() if _ not in no_delete ]
        for _ in delete:
            _min_id_ = -1
            _min_len_ = math.inf
            del _action_board_ [_]

        _mine_board_ = [int(j) for j in input().split()]
        _opp_board_ = [int(j) for j in input().split()]

        # SETUP
        _mine_.setup_4( _mine_board_ )
        _mine_.setup_6( _learn_board_ )
        if _learn_id_ != -1 :
            #_mine_.setup_5( _mine_agent_ )
            for _ in _mine_agent_.values():
                _mine_.setup_8( _ )

        # SETUP
        for _ in _action_board_.values():
            if len(_._predict) == 0 :
                #_.memento = _
                _.state = _mine_board_[:]
                _.cast = copy.copy(_mine_.cast)
                _mine_.attach_compute( _ )
            else :
                #
                s1 = _mine_board_[:]
                e1 = False
                for c1 in _._predict:
                    if f_type(c1.param) == 2 :
                        e1 = True
                        break

                    r1 = c1.spell(s1)
                    min1 = sum([1 for i1 in r1[0:4] if i1 < 0])
                    max1 = sum(r1[0:4])

                    if min1 > 0 or max1 > 10 :
                        e1 = True
                        break

                    s1 = r1

                if e1 == True:
                    #_.memento = _
                    _.state = _mine_board_[:]
                    _.cast = copy.copy(_mine_.cast)
                    _._predict, _.k = [] , 999
                    _mine_.attach_compute( _ )

        # SEARCH
        _learn_id_ = -1
        _learn_k1_ = -1

        for _learn_k1_, _ in zip([0,1,2,3],_learn_board_):

            if _mine_board_[0] < _learn_k1_:
                break

            if f_id(_.param) in k_2know:
                _learn_id_ = f_id(_.param)
                for k1, _ in _action_board_.items() :
                    _._predict = []
                    _mine_.detach_compute( _ )
                break

        if _learn_id_ == -1 :
            _learn_id_ , _learn_k1_ = _mine_.compute_4()

        if _learn_id_ != -1 :
            LEARNED = LEARNED + 1

        elif len(_mine_.observer) > 0 :
            _mine_.compute_3()

            _min_id_, _min_len_ = -1, -math.inf
            for k1, _ in _action_board_.items() :

                if len(_._predict) > 0 :
                    s1 = ( f_price(_.action.param) * 30 ) // _.k

                    if s1 > _min_len_:
                        _min_len_, _min_id_ = s1, k1

            if _min_id_ == -1 :
                pass

            elif f_type(_action_board_[_min_id_]._predict[0].param) == 2 :
                _learn_id_ = f_id(_action_board_[_min_id_]._predict[0].param)
                _learn_k1_ = next(iter([i1 for i1,_ in zip([0,1,2,3,4,5],_learn_board_) if f_id(_.param) == _learn_id_ ]))
                _action_board_[_min_id_].k = 1

        # OUT
        if _learn_id_ != -1 :

            _ = _learn_board_[_learn_k1_]

            print(_.read())

        elif _min_id_ != -1 :

            _ = _action_board_[_min_id_].predict()
            _action_board_[_min_id_].k = 1

            if _ in _mine_.cast :

                _mine_.cast = set()

                print('REST')

            elif f_repeat(_.param) == 1 :

                nb = 0
                for spell1 in _action_board_[_min_id_]._predict:
                    if _ == spell1 :
                        nb = nb + 1
                    else :
                        break

                print(f'{_.read()} {nb}')

                _mine_.cast.add( _ )

                for k1, a1 in _action_board_.items():

                    if k1 == _min_id_:
                        for i1 in range(nb):
                            a1.update(None)

                    else:
                        if _ in a1._predict :
                            a1._predict.remove(_)
                            a1.k = max( (a1.k - _.gain() ) , 1 )

            else :

                print(_.read())

                _mine_.cast.add( _ )

                for k1, a1 in _action_board_.items():

                    if k1 == _min_id_:
                        a1.update(None)
                    else:
                        if _ in a1._predict :
                            a1._predict.remove(_)
                            a1.k = max( (a1.k - _.gain() ) , 1 )


        else :

            s1 = _mine_.state[:]

            i1 = inv_inv2int( [ FUZZY_GET[i1] for i1 in f_state(s1) ] )

            t1 = _mine_.spell[:]

            max1 = -1
            keep1 = None
            for _ in t1[i1]:

                if _ in _mine_.cast: continue
                if _.gain() > max1: keep1 = _

            if keep1 is None :
                print('REST')
                _mine_.cast = set()
            else:
                print( keep1.read())
                _mine_.cast.add( keep1 )
