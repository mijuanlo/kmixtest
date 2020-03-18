from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from time import time

from .Util import mychr, unmychr, Color, Direction
from .Config import _

class Resolver(QObject):
    # class testclass:
    #     A = '00 00 10 11 01 10 00 01 01'
    #     # A 0 0
    #     # B 0 0
    #     # C 1 0
    #     # D 1 1
    #     # E 0 1
    #     # F 1 0
    #     # G 0 0
    #     # H 0 1
    #     # I 0 1

    def dprint(self,msg,found):
        if self.debug_level < 2:
            return
        if not msg:
            msg = "<{}>".format(_('empty'))
        if found is True:
            msg = Color.makecolor(msg,Color.GREEN)
        elif found is None:
            msg = Color.makecolor(msg,Color.YELLOW)
        else:
            msg = Color.makecolor(msg,Color.RED)
        qDebug(msg)

    def __init__(self,*args,**kwargs):
        super().__init__()
        self.terminate = False
        self.killing = False
        thing = kwargs.get('thing',None)
        complete = kwargs.get('complete',None)
        debug_level = kwargs.get('debug_level',None)
        for i,value in enumerate(args,1):
            if i == 1 and not thing:
                thing = value
            if i == 2 and not complete:
                complete = value
            if i == 3 and not debug_level:
                debug_level = value

        if not complete:
            complete = False
        if not debug_level:
            debug_level = 0
        self.thing = thing

        self.complete = complete

        self.debug_info = { 'counter' : {'partial':0,'full':0}, 'times' : [] }
        self.debug_level = debug_level
        
        self.combination = ''
        self.levels = 0
        self.options = {}
        self.results = []
        self.conditions = []
        if not self.initialize(self.thing):
            print(Color.makecolor(_('Not valid'),Color.RED))
            exit(1)

    def abort(self):
        if self.debug_level > 0:
            qDebug(_('Aborting resolver'))
        self.terminate = True
    def reset(self):
        if self.debug_level > 0:
            qDebug(_('Killing resolver'))
        self.killing = True
    # function to print metric counters when debugging
    def print_debug_info(self):
        if self.debug_level > 0:
            acu = 0.0
            s = []
            for ini,end in self.debug_info['times']:
                cur = end-ini
                acu += cur
                s.append('{0:4.2f}'.format(cur))
            qDebug("{0:s}: {1:10d}/{2:<10d} [ {3:s} {4:4.2f} {5:s} ] [{6:s}]".format(_('Checks'),self.debug_info['counter']['partial'],self.debug_info['counter']['full'],_('TOTAL'),acu,_('seconds'),'+'.join(s)))

    def print_conditions(self):
        s = '{}:\n'.format(_('Conditions'))
        for c,places in self.conditions:
            strplaces = [ str(x) for x in places ]
            s += '{} --> {}\n'.format(c,','.join(strplaces))
        qDebug(s)
    
    # Configure conditions into resolver, conditions represent questions that resolver try to answer with valid combination
    # Example) if we want to answer if one row can go down, i will add one or more conditions that this row need to be on any of target rows
    #
    # Parameters:
    # item: string with one or more characters representing rows
    # direction: enum setting direction
    def addCondition(self,item,direction):
        if item in self.options['names'] and self.options['names'][item]['linked']:
            stop = 1
        self.killing = False
        item_tmp = ''
        # If item is a linked item, link all elements into condition
        
        is_linked = False
        size_linked = 0
        for i in item:
            if self.options['names'][i].get('linked'):
                is_linked = True
                linked_str = ''.join(self.options['names'][i].get('list'))
                size_linked = len(linked_str)
                if linked_str not in item_tmp:
                    item_tmp += linked_str
            else:
                item_tmp += i
        item = item_tmp
        
        #linked_conditions = [ x for x in item if self.options['names'][x]['linked'] ]
        
        # Get starting item position
        i = self.combination.index(item)
        
        fixed = [x for x in self.options['places'] if self.options['places'][x]]
        # If fixed position, add condition with only one possible position for each

        if direction == Direction.FIXED:
            i+=1
            for x in item:
                self.conditions.append((x,[i]))
                i+=1
        # If is going up, add a list of possible positions for each element
        elif direction == Direction.UP:
            offset=-1
            for x in item:
                offset+=1
                l = list(range(i+offset,-1+offset,-1))
                # Conditions going up need to be reversed with nearest (greatest) positions first
                holes = []
                acu = []
                if is_linked:
                    # search for holes
                    for li in l:
                        if li in fixed:
                            acu = []
                            continue
                        acu.append(li)
                        
                        if len(acu) >= size_linked:
                            acu = [ j for j in acu if j not in holes ]
                            holes.extend(acu)
                            
                if is_linked:
                    if not holes:
                        # make impossible
                        holes = [-1]
                    # else:
                    #     for j in range(size_linked-1-item.index(x),0,-1):
                    #         del holes[0]
                    l = holes
                else:
                    # Remove fixed
                    l = [ x for x in l if x not in fixed]

                self.conditions.append((x,l))

        # If is going down, add a list of possible positions for each element
        elif direction == Direction.DOWN:
            offset=1
            for x in item:
                offset+=1
                l = list(range(i+offset,self.levels+2))
                # Conditions going down need to be growing with nearest (lowest) positions first
                holes = []
                acu = []
                if is_linked:
                    # search for holes
                  
                    for li in l:
                        if li in fixed:
                            acu = []
                            
                            continue
                        acu.append(li)
                        
                        if len(acu) >= size_linked:
                            acu = [ j for j in acu if j not in holes ]
                            holes.extend(acu)

                if is_linked:
                    if not holes:
                        # make impossible
                        holes = [-1]
                    # else:
                    #     for j in range(offset,2,-1):
                    #         del holes[0]
                    l = holes
                else:
                # Remove fixed
                    l = [ x for x in l if x not in fixed]
                self.conditions.append((x,l))

    # Check if it's valid combination
    # Combination (thing) can be complete or partial combination, this function validate partial combination to avoid go through 
    # branches that wouldn't end succesfully because conditions applied over partial combination are failed
    #
    # This function ends with 3 results:
    # False: Wrong combination(thing), expansion tree needs to be cut
    # None: Not wrong combination until now, but it's not complete, any possible result can be found later in this branch
    # True: Good combination was found, this combination agree all condition and it's full lenght
    def validate(self,thing):
        l = len(thing)
        # It's full when it's at lowest level of recursion configured
        full = l == self.levels

        # Debug counters
        if self.debug_level > 0:
            if full:
                self.debug_info['counter']['full'] += 1
            else:
                self.debug_info['counter']['partial'] += 1
        if self.debug_info['counter']['full'] > 200000:
            print('POSSIBLE ERROR/'*20)
            exit(0)

        # First validation, combination it's empty
        if not thing:
            self.dprint(thing,None)
            return None
        # Check dynamic conditions
        for id,valid in self.conditions:
            if id==thing[l-1]:
                if l not in valid:
                    self.dprint(thing,False)
                    return False
        # Check base conditions (fixed or linked)
        option = self.options['names'].get(thing[l-1])
        if option.get('fixed') and option.get('place') != l and self.options['places'][l] != thing[l-1]:
            self.dprint(thing,False)
            return False
        # Check base conditions linked
        for t in thing:
            option = self.options['names'].get(t)
            if option.get('linked'):
                idx = None
                for x in [ o for o in option.get('list') ]:
                    if idx == None:
                        if x in thing:
                            idx = thing.index(x)
                            continue
                        else:
                            # Wrong order for linked items
                            self.dprint(thing,False)
                            return False
                    else:
                        idx += 1

                    if idx >= l:
                        break
                    if x != thing[idx]:
                        self.dprint(thing,False)
                        return False

        # If it's full, one solution was found
        if full:
            if self.debug_level > 0:
                self.debug_info['times'].append((self.stime,time()))
                self.stime = time()
            self.dprint(thing,True)
            # If self.complete, this is a exhaustive search with all results and need to continue recursion over the tree
            # If self.complete, results are stored
            self.results.append(thing)
            if self.complete:
                return None
            # If only need a first valid solution, return that solution ending recursion
            else:
                return thing
        # if not full, and not returned before, it's going well
        else:
            self.dprint(thing,None)
            return None
    def reorder(self,used,possible):
        out = possible.copy()
        level = len(used)
        i = level

        for cond,places in self.conditions:
            if cond not in possible:
                continue
            if not len(places):
                continue
            first = places[0]
            out.insert(first-level,cond)
        # rep = []
        # delete = []
        # for i in range(len(out)):
        #     if out[i] in rep:
        #         delete.append(i)
        #     else:
        #         rep.append(out[i])
        # for i in delete:
        #     del out[i]
        out = list(dict.fromkeys(out))

        # for x in range(len(possible)):
        #     if out[x] != possible[x]:
        #         print('{}\n{}'.format(possible,out))
        #         print('/CHANGE/REORDER'*10)
        
        if len(possible) != len(out):
            qDebug(_('Error'))
            exit(1)
        return out
    # Reorder apply heuristic over possible recursion branches, improving time to answer and finding solution
    # DISABLED FUNCTION
    # def reorder(self,used,possible):
    #     out = []
    #     level = len(used)
    #     # Try to use first whatever that has conditions applied and it's not used
    #     l=[elem for elem,places in self.conditions]
    #     for p in possible:
    #         if p in used:
    #             raise ValueError('Can\'t reorder {} because it\'s used and try to mark as possible'.format(p))
    #         if p not in l:
    #         # not conditionated elements insert at the end
    #             out.append(p)
    #         else:
    #             # conditionated elements first , try to get quickly fail or success
    #             for elem,places in self.conditions:
    #                 if p == elem:
    #                     if not len(places):
    #                         raise ValueError('Condition without candidate position')
    #                     if level in places:
    #                         out.insert(0,p)
    #                     else:
    #                         out.append(p)
        
    #     # Assertion that list of possible elements for selecting next branch is the same reordered
    #     if len(possible) != len(out):
    #         qDebug('Error')
    #         exit(1)
    #     return out

    # tree function makes recursive tree trying to find a valid combination
    # Parameters:
    # level: actual recursion level
    # used: combination used at this point of branch
    # initialcall: flag to identify if it's a recursive call or not, debugging purposes
    def tree(self,level=1,used='',initialcall=True):
        # Allow abort recursion when program exit
        if self.terminate:
            return
        if self.killing:
            return
        # Allow process qt events
        QCoreApplication.processEvents()
        QCoreApplication.sendPostedEvents()

        # Debugging metric counters
        if initialcall and self.debug_level > 0:
            self.stime = time()

        # Validate actual combination
        ret = self.validate(used)

        # If actual combination it's valid and it's partial solution (more elements need to be placed)
        if ret is None and level <= self.levels:
            # Check if this level has a fixed value specified from user selection
            dyn_con = [ x for x,y in self.conditions if len(y)==1 and y[0] == level ]
            if self.options['places'][level] or dyn_con:
                candidate = self.options['places'][level]
                if not candidate:
                    candidate = dyn_con.pop()
                ret = self.tree(level+1,used+candidate,False)
                if ret:
                    if initialcall and self.debug_level > 0:
                        self.debug_info['times'].append((self.stime,time()))
                    return ret
            # If this level(position) hasn't fixed value, need to run exhaustive recursion tree over actual combination
            else:
                possible = []
                if used and self.options['names'][used[-1]]['linked']:
                    l = self.options['names'][used[-1]]['list']
                    possible = [ o for o in l if o not in used ]
                if len(possible) == 0:
                    # possible values are: whatever element if not used until now and not fixed on any position,
                    possible = [ o for o in self.options['names'] if o not in used and o not in self.options['places'] ]
                    # optimize order of branches, selecting more probable branch first
                    # disabled function
                    #possible = self.reorder(used,possible)
                # launch recursion tree
                for x in possible:
                    ret = self.tree(level+1,used + x,False)
                    # if returns combination(string), one value was found (evaluated as True), ends recursion
                    # if returns False, wrong value (evaluated as False), continue recursion
                    # if returns None, partial good result, continue recursion
                    if ret:
                        if initialcall and self.debug_level > 0:
                            self.debug_info['times'].append((self.stime,time()))
                        return ret
        # validation was failed or result is found
        else:
            if initialcall and self.debug_level > 0:
                self.debug_info['times'].append((self.stime,time()))
            return ret

        # validation evaluates good result until now
        if initialcall and self.debug_level > 0:
            self.debug_info['times'].append((self.stime,time()))

    # Initialize resolver structures
    # Parameter:
    # thing: string representation of table and user base conditions (fixed or linked)
    # Example) 
    #   - Each row is represented with two values (first (fixed), second (linked))
    #   - Each value is: (1 (true) or 0 (false))
    #
    #   Example table with 4 rows, first fixed, second normal, three an fouth linked
    #   thing = '10000101' or something as '10 00 01 01' or '10-00-01-01'...
    def initialize(self,thing):
        # Parse non desired characters (only 1 and 0)
        try:
            skip_characters = [x for x in thing if x not in '01' ]
            for x in skip_characters:
                thing = thing.replace(x,'')
        except:
            pass
        l = len(thing)
        # not empty thing and with odd values it's needed
        wellformed = l%2 == 0 and l!=0
        if not wellformed: 
            return False
        else:
            self.thing = thing
        # dynamic conditions for asking questions
        self.conditions = []
        self.combination = ''
        # options: stores table representation and characteristics or properties,
        #  'places' are fixed positions selected by the user,
        #  'names' are each row properties
        self.options = { 'places': {} , 'names': {} }
        
        # levels configures height of expansion tree of possible options into recursive calls
        # levels it's a number of rows from table
        self.levels = int(len(thing)/2)
        templinked = []
        fixedlist=False

        #if self.debug_level > 1:
        #    table = '--- TABLE ---\n'
        for i in range(self.levels):
            # each row has a string representation of one ascii character, example: three rows -> ABC
            name = mychr(i)
            self.combination += name
            mark_fixed = thing[2*i]
            mark_linked = thing[2*i+1]
            #if self.debug_level > 1:
            #    table += '{}   | {} | {} |\n'.format(name,mark_fixed,mark_linked) 

            # built structure stores:
            #  actual position (place): int
            #  it's mark as fixed by user (ownfixed): bool
            #  it's mark as linked by user (linked): bool
            #  list of all linked group elements (list): list(int)
            #  flag if it's part of linked elements that are fixed, because any or all elements was mark as fixed by user (fixedlist): bool
            #  flag if it's fixed by any reason (fixed by user (ownfixed) or linked with some other that is fixed by user): bool (performs OR operation over 'ownfixed' and 'list' searching 'ownfixed')
            self.options['names'].setdefault(name,{'place':i+1,'ownfixed':mark_fixed=='1','linked':mark_linked=='1','list':[],'fixedlist':None,'fixed':None})
            
            # Complete structure iterating over linked elements
            if self.options['names'].get(name).get('linked'):
                templinked.append(name)
            else:
                for char in templinked:
                    if self.options['names'][char]['ownfixed']:
                        fixedlist = True
                    self.options['names'][char]['list']=templinked
                if fixedlist:
                    for char in templinked:
                        self.options['names'][char]['fixedlist'] = True
                templinked = []
                fixedlist = False
        #if self.debug_level > 1:
        #    table += '-------------\n'
        #    print(Color.makecolor(table,Color.YELLOW)
        
        # Complete structure iterating over linked elements
        # (this code is for last element not covered into loop)
        if templinked:
            for char in templinked:
                self.options['names'][char]['list']=templinked
                if self.options['names'][char]['ownfixed']:
                    fixedlist = True
            if fixedlist:
                    for char in templinked:
                        self.options['names'][char]['fixedlist'] = True
            templinked = False
            fixedlist = False
        for char in self.options['names']:
            self.options['names'][char]['fixed'] = self.options['names'][char]['ownfixed'] or self.options['names'][char]['fixedlist']
        
        # Build 'places' structure with fixed positions
        for i in range(self.levels):
            name = mychr(i)
            if self.options['names'][name]['fixed']:
                self.options['places'][i+1] = name
            else:
                self.options['places'][i+1] = None
        self.killing = False
        return True

    # Get internal stored found results 
    def getResults(self):
        return self.results

    # function for debug recursion showing results
    def print_results(self):
        results = len(self.results)
        if not results:
            r = _('No solution')
        else:
            r = ','.join(self.results)
            if self.complete:
                r += ' ({} {})'.format(results,_('results'))
            else:
                r += ' ({})'.format(_('first result'))
        if self.debug_level > 0:
            qDebug(Color.makecolor(r,Color.BLUE))
        # Print metric counters
        self.print_debug_info()
