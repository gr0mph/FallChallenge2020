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

CORRECT_REST = 0
CORRECT_BREW = 1
CORRECT_CAST = 2
CORRECT_LEARN = 3

PREDICT_MINE = 0
PREDICT_OPP = 1

_action_board_ = {}
_opp_brew_ = {}
_learn_board_ = []

_mine_board_ = [ 0 , 0 , 0 , 0 , 0 ]
_opp_board_ =  [ 0 , 0 , 0 , 0 , 0 ]

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
        print(f'learn {self} f_tax{f_tax(self.param)} f_tome {f_tome(self.param)}', file=sys.stderr)
        return min( ( f_tax(self.param) - f_tome(self.param)) , 4 ) + 1

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
        self.cast, self.state, self.learn = set(), [ 0 , 0 , 0 , 0 , 0], []
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

        for i2 , _ in zip([0,1,2,3,4,5], self.learn[ 0 : 1 ]):

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

    def setup_4(self,state):
        self.state = state[:]

    def setup_6(self, learn):
        self.learn = learn[:]

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

    def setup_9( self , cast ):

        if cast[0] == CORRECT_BREW:
            pass

        elif cast[0] == CORRECT_REST:
            self.cast = set()

        elif cast[0] == CORRECT_LEARN:
            pass

        elif cast[0] == CORRECT_CAST:

            for _ in self.learned:
                if _ not in self.cast:
                    if f_repeat(_.param) == 0 :
                        s1 = _.spell( self._memento.state )
                        c1 = sum( [abs(i1-i2) for i1,i2 in zip(s1[0:4],self.state[0:4]) ])
                        if c1 == 0 :
                            self.cast.add( _ )
                            return

                    else:
                        _repeat_ = True
                        s1 = self._memento.state[:]
                        while _repeat_ :
                            s1 = _.spell(s1)
                            c1 = sum( [abs(i1-i2) for i1,i2 in zip(s1[0:4],self.state[0:4]) ])
                            if c1 == 0 :
                                self.cast.add( _ )
                                return
                            c1 = sum( [ 1 for i1 in s1[0:4] if i1 < 0 ] )
                            if c1 > 0 :
                                _repeat_ = False

            pass

    def attach_compute(self,instance):
        if instance not in self.observer :
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
            self.state = clone.state
            self.action, self.spell = clone.action, clone.spell
            self.k = clone.k
        else :
            self.state = []
            self.action, self.spell = None, []
            self.k = 999

        self._predict = copy.copy(clone._predict) if clone is not None else []
        self._memento = clone._memento if clone is not None else self

    def check_3( self , caller , versus, gain , state , predict ):
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
        self._memento.spell = setter.spell
        self._memento.action = setter.action
        self._memento.state = setter.state[:]

        self._memento = copy.copy(setter)
        self._memento._predict = copy.copy(setter._predict)

    def correction(self,state):
        pass

################################################################################
#
################################################################################

def detach_observer( obj1 , obj2 , versus1 , gain1 , state1 , predict1 ):

    delete1 = []
    delete2 = []

    for update in obj1.observer:

        if update.check_3( obj1 , versus1 , gain1 , state1 , predict1 ) is not None :

            delete1.append( update )

            id1 = f_id(update.action.param)

            outdate = [outdate for outdate in obj2.observer if f_id(outdate.action.param) == id1]

            if len(outdate) > 0 :

                delete2.append( outdate[0] )

    for update in delete1 :
        obj1.detach_compute(update)

    for outdate in delete2 :
        obj2.detach_compute(outdate)

def predict_compute( me , you ):

    resolve = []
    already = set()
    search_turn = 1

    already_add = already.add
    already_remove = already.remove
    heapq_heappush = heapq.heappush
    heapq_heappop = heapq.heappop

    # ME

    s1, t1, c1, p1 = me.state[:] , me.spell[:] , copy.copy(me.cast) , []

    g1, d1, v1 = 1, f_quality(s1) , PREDICT_MINE * 100 + len(c1)

    already_add( ( g1 , d1 , v1 ) )

    heapq.heappush( resolve , ( g1 , d1 , v1 , s1 , t1 , c1 , p1 ) )

    # YOU

    s1, t1, c1, p1 = you.state[:] , you.spell[:] , copy.copy(you.cast) , []

    g1, d1, v1 = 1, f_quality(s1) , PREDICT_OPP * 100 + len(c1)

    already_add( ( g1 , d1 , v1 ) )

    heapq.heappush( resolve , ( g1 , d1 , v1 , s1 , t1 , c1 , p1 ) )

    while len(resolve) > 0 and search_turn < 600 :

        search_turn = search_turn + 1

        g1 , d1 , v1 , s1 , t1 , c1 , p1 = heapq_heappop(resolve)

        already_remove( ( g1 , d1 , v1 ) )

        if v1 == PREDICT_MINE :
            detach_observer( me , you , v1 , g1 , s1 , p1 )

        elif v1 == PREDICT_OPP :
            detach_observer( you , me , v1 , g1 , s1 , p1 )

        if len(me.observer) == 0 and len(you.observer):
            break

        i1 = inv_inv2int( [ FUZZY_GET[i1] for i1 in f_state(s1) ] )

        a1 = t1[i1]
        if g1 == 1 and v1 == PREDICT_MINE :

            if TURN < 6 :

                a1 = me.learn[ 0 : 3 ]

            else :

                a1 = me.learn[ 0 : 2 ] + t1[i1]

        for _ in a1 :

            next_g1, next_d1, next_v1 = g1, d1, v1

            next_s1, next_t1, next_c1, next_p1 = s1, t1, c1, p1

            _in_repeat_ = False

            while _ in a1:

                next_s1 = _.spell(next_s1)

                next_p1 = next_p1[:]

                next_p1.append( _ )

                if _in_repeat_ == True :

                    next_g1 = next_g1 - _.gain()

                    next_d1 = f_quality(next_s1)

                    next_v1 = (next_v1 // 100) * 100 + len(next_c1)

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

                    next_d1 = f_quality(next_s1)

                    next_v1 = (next_v1 // 100) * 100 + len(next_c1)

                if ( next_g1 , next_d1 , next_v1 ) not in already and sum(next_s1[0:4]) <= 10 :

                    next_t1 = next_t1

                    if f_type(_.param) == 2 and next_v1 == PREDICT_MINE :

                        next_t1 = me.setup_7( _ , next_t1 )

                    already_add( ( next_g1 , next_d1 , next_v1 ) )

                    heapq_heappush( resolve , ( next_g1 , next_d1 , next_v1 , next_s1 , next_t1 , next_c1 , next_p1 ) )

                if f_type(_.param) != 2 and f_repeat(_.param) == 1 :

                    i1 = inv_inv2int( [ FUZZY_GET[i1] for i1 in f_state(next_s1) ] )

                    a1 = next_t1[i1]

                    _in_repeat_ = True

                else:
                    break

################################################################################
#
################################################################################

k_2know = [ 2 , 3 , 4 , 12 , 13 , 14 , 15 , 16 ]
# TODO list gain 3 , list gain 4 , list ...

if __name__ == '__main__':

    _min_id_ , _opp_id_ = -1 , -1
    _min_len_ , _opp_len = math.inf, math.inf

    _learn_id_ = TURN
    _opp_learn_ = None


    _mine_ = KanbanBoard(None)
    _opp_ = KanbanBoard(None)
    _opp_._memento = KanbanBoard(None)

    while True:
        TURN = TURN + 1
        out = ''

        no_delete = []
        _learn_board_ = []
        _opp_cast_ = []
        for i in range( int(input()) ):
            _ = input().split()

            _[0], _[1], _[2:] = int(_[0]), TYPE_SET[_[1]], map(int,_[2:])

            if f_type(_) == TYPE_CAST :
                if f_id(_) not in _mine_agent_:
                    _mine_agent_[ f_id(_) ] =  SpellNeuron( tuple(_) )
                    _min_id_ = -1
                    _min_len_ = math.inf
                    for _ in _action_board_.values(): _.k, _._predict = 999, []

            elif f_type(_) == TYPE_OPP_CAST :
                if f_id(_) not in _opp_agent_:
                    _opp_agent_[ f_id(_) ] = SpellNeuron( tuple(_) )
                    _opp_id_ = -1
                    _opp_len_ = math.inf
                    _opp_learn_ = _opp_agent_[ f_id(_) ]
                    for o1 in _opp_brew_.values(): o1.k, o1._predict = 999, []

            elif f_type(_) == TYPE_LEARN :
                _learn_board_.append( LearnNeuron( tuple(_) ) )

            elif f_type(_) == TYPE_BREW and _[0] in _action_board_ :
                no_delete.append( _[0] )

            elif f_type(_) == TYPE_BREW :
                no_delete.append( _[0] )
                _action_board_ [ _[0] ] = AgentBoard(None)
                _action_board_[ _[0] ].action = BrewNeuron( tuple(_) )
                _opp_brew_[ _[0] ] = AgentBoard(None)
                _opp_brew_[ _[0] ].action = BrewNeuron( tuple(_) )
                for _ in _opp_brew_.values(): _.k, _._predict = 999, []

        delete = [ _ for _ in _action_board_.keys() if _ not in no_delete ]
        for _ in delete:
            _min_id_, _opp_id_ = -1 , -1
            _min_len_, _opp_len_ = math.inf , math.inf
            del _action_board_ [_]
            del _opp_brew_ [_]

        _mine_board_ = [int(j) for j in input().split()]

        _opp_.memento = _opp_

        _opp_board_ = [int(j) for j in input().split()]

        if _opp_learn_ is not None :
            _opp_cast_ = tuple( [ CORRECT_LEARN , _opp_learn_ ] )

        elif _opp_board_[4] > _opp_._memento.state[4] :
            _opp_cast_ = tuple( [ CORRECT_BREW , None ] )

        elif sum( [ abs(i1 - i2) for i1,i2 in zip(_opp_board_[0:4],_opp_._memento.state[0:4]) ] ) == 0 :
            _opp_cast_ = tuple( [ CORRECT_REST , None ] )

        else :
            _opp_cast_ = tuple( [ CORRECT_CAST , None ] )

        # SETUP
        _mine_.setup_4( _mine_board_ )
        _opp_.setup_4( _opp_board_ )
        _mine_.setup_6( _learn_board_ )
        _opp_.setup_6( _learn_board_ )

        if _learn_id_ != -1 :
            for _ in _mine_agent_.values():
                _mine_.setup_8( _ )

        if _opp_learn_ is not None :
            for _ in _opp_agent_.values():
                _opp_.setup_8( _ )

        _opp_.setup_9( _opp_cast_ )
        _opp_learn_ = None

        # SETUP
        for _ in _action_board_.values():
            if len(_._predict) == 0 :
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
                    _.state = _mine_board_[:]
                    _.cast = copy.copy(_mine_.cast)
                    _._predict, _.k = [] , 999
                    _mine_.attach_compute( _ )

        # SETUP
        for _ in _action_board_.values():
            _.state = _opp_board_[:]
            _.cast = copy.copy
            _mine_.attach_compute( _ )

        # SETUP
        for _ in _opp_brew_.values():
            _.state = _opp_board_[:]
            _.cast = copy.copy
            _opp_.attach_compute( _ )

        # SEARCH
        _learn_id_ = -1
        _learn_k1_ = -1

        for _learn_k1_, _ in zip([0,1,2],_learn_board_):

            if _mine_board_[0] < _learn_k1_:
                break

            if f_id(_.param) in k_2know:
                _learn_id_ = f_id(_.param)
                for k1, _ in _action_board_.items() :
                    _._predict = []
                    _mine_.detach_compute( _ )
                break

        if _learn_id_ != -1 :
            LEARNED = LEARNED + 1

        elif len(_mine_.observer) > 0 :
            predict_compute ( _mine_ , _opp_ )

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
