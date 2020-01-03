from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from .Resolver import Resolver
from .Config import DEBUG_LEVEL
from .Util import mychr, unmychr, Direction, Color

# Class that make a cache over resolver improving speed with already called combinations
# This class it's needed cause resolver is called from update graphic functions from gui
#
# Cache stores results from resolver into dictionary, with key built with compound table state and conditions (queries + assertions from user)
class ResolverCached(QObject):
    cache = {}

    def __init__(self,*args,**kwargs):
        super().__init__()
        global DEBUG_LEVEL
        self.terminate = False
        self.killing = False
        self.debug_level = DEBUG_LEVEL
        self.terminate = False
        self.resolver = None
        self.fullreset()
    
    def abort(self):
        if self.debug_level > 0:
            qDebug("Aborting resolver cached")
        self.terminate = True
        if self.resolver:
            self.resolver.abort()

    # get results from cache or run a recursive resolver
    def getResults(self,*args,**kwargs):
        if kwargs.get('debug'):
            global DEBUG_LEVEL
            DEBUG_LEVEL=2
            self.debug_level=2
            this_is_for_putting_debug_breakpoint_call_is_replaying=True
            # Remove key from cache
            key = self.makekey()
            if key in self.cache:
                del self.cache[key]
        if not self.terminate and not self.killing:
            # get the cache key for current state
            k = self.makekey()
            if not k or not k in self.cache:
                # run expansion tree with resolver, when resolver ends, results are stored into cache
                self.tree()
            # return result from cache
        if not self.terminate and not self.killing:
            return self.cache[k]
        return None

    # Make a new resolver initialized
    def newQuery(self,*args,**kwargs):
        self.killing = False
        if not self.terminate:
            self.resolver = Resolver(*args,**kwargs)
            self.key = self.resolver.thing
            self.key_result = ''
            self.conditions = {}

    # Reset all
    def fullreset(self,*args,**kwargs):
        self.cache = {}
        self.reset()

    # Reset conditions but not cached results
    def reset(self,*args,**kwargs):
        self.key_result = ''
        self.conditions = {}
        if self.resolver:
            self.killing = True
            self.resolver.reset()

    # Make a cache key built from table state and dynamic conditions
    # Parameters:
    # inserting: flag to set conditions into full resolver
    def makekey(self,inserting=False):
        self.key_result = self.key
        for t in sorted(list(self.conditions)):
            for d in sorted(list(self.conditions[t])):
                if inserting:
                    self.resolver.addCondition(t,d)
                self.key_result += str(t) + str(d)
        return self.key_result

    # Recursive call to run resolver if not exists one cached key
    def tree(self):
        # Calculates key
        if not self.terminate:
            k = self.makekey()
            if k not in self.cache:
                # Configure conditions into resolver
                k = self.makekey(inserting=True)
                if self.debug_level > 1:
                    self.resolver.print_conditions()
                # Run resolver
                self.resolver.tree()
                # Print results from resolver
                self.resolver.print_results()
                # Stores into cache the results
                if not self.killing:
                    self.cache[k] = self.resolver.getResults()
    
    # Stores dynamic conditions (queries) for running resolver
    # Need conditions (questions and tablestate) to query cache
    def addCondition(self, thing, dir):
        # Conditions (queries) are stored as dictionary keys
        # Example) Row 'B' need to go down -> we are querying if B can go down -> { 'B' : { 1 : {} } }
        self.conditions.setdefault(thing,{})
        self.conditions[thing].setdefault(dir,{})

    def get_row_value(self,state, row, column):
        FIXED_COLUMN = 0
        LINKED_COLUMN = 1
        try:
            return True if state[(row*2)+column] == '1' else False
        except:
            return False
    def row_is_linked(self, state, row):
        LINKED_COLUMN = 1
        return self.get_row_value(state,row,LINKED_COLUMN)
    def row_is_fixed(self, state, row):
        FIXED_COLUMN = 0
        return self.get_row_value(state,row,FIXED_COLUMN)

    def configureResolver(self, state, row, direction):
        ROW_COUNT = int(len(state)/2)

        # row to id representing row into resolver
        ID = mychr(row)
        
        # starts new cachedresolver for query state & conditions
        self.newQuery(thing = state, complete = False, debug_level = self.debug_level)
        # add query (as condition) to get answer if one row can move or not
        self.addCondition(ID,direction)

        #
        # Optimization conditions (specially going up, because going down recursion is easiest)
        #
        # If query if one row can go up, maybe down rows can be fixed
        if direction == Direction.UP:
            # rows fixed for optimization
            s = ''
            # row pointer
            r = row
            # count bottom linked rows
            count=0
            # count down rows that are linked
            for i in range(r-1,-1,-1):
                if self.row_is_linked(state,i) and not self.row_is_fixed(state,i):
                    count+=1
            # move row pointer to end linked element (if current ID it's linked)
            while r < ROW_COUNT and self.row_is_linked(state,r):
                r += 1
            # move row pointer to allow down row linked elements going up
            while r < ROW_COUNT and count > 0 and not self.row_is_linked(state,r) and not self.row_is_fixed(state,r):
                r += 1
                count-=1
            # build condition for remaning rows
            for i in range(r,ROW_COUNT):
                s += mychr(i)
            # remove current row to avoid duplicate condition on selected row
            s = s.replace(ID,'')
            # add optimization conditions
            if s:
                self.addCondition(s,Direction.FIXED.value)
        # If query if one row can go down, maybe up rows can be fixed
        if direction == Direction.DOWN:
            # rows fixed for optimization
            s = ''
            # row pointer
            r = row
            # count upper linked rows
            count = 0
            # count upper rows that are linked
            for i in range(r+1,ROW_COUNT):
                if self.row_is_linked(state,i) and not self.row_is_fixed(state,i):
                    count+=1
            # move row pointer to first element linked if ID it's linked
            while r > -1 and self.row_is_linked(state,r):
                r -= 1
            # move row pointer to allow upper elements go down
            while r > -1 and count > 0 and not self.row_is_linked(state,r) and not self.row_is_fixed(state,r):
                r -= 1
                count-=1
            # build condition for remaning rows
            for i in range(r,-1,-1):
                s = mychr(i)+s
            # remove current row to avoid duplicate condition on selected row
            s = s.replace(ID,'')
            # add optimization conditions
            if s:
                self.addCondition(s,Direction.FIXED.value)
