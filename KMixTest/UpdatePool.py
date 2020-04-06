from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from queue import Queue, Empty

from .Config import _, DEBUG_LEVEL, NATIVE_THREADS, TIMER_QUEUE, NUM_THREADS
from .Worker import Worker
from .Util import Direction, Color

class UpdatePool(QObject):
    newResult = Signal(int,int,str)
    modelItemSize = 6
    modelStateOffset = 2
    modelResultOffset = 4
    def __init__(self,parent):
        global DEBUG_LEVEL, NATIVE_THREADS, TIMER_QUEUE
        self.debug_level = DEBUG_LEVEL
        QObject.__init__(self)
        self.parent = parent
        global NUM_THREADS
        # Possible job queue
        self.jobs = Queue(10000)
        # Jobs timed enqueued for run
        self.dispatched = Queue(10000)
        self.workers = []
        # Model for movements list of rows, row with (upstate,downstate,updatestate)
        self.model = {}
        # Model lock
        self.lock = QMutex()

        self.stateString = ''
        self.levels = 0

        self.newResult.connect(self.newResultCompleted)

        if NATIVE_THREADS:
            self.threadpool = QThreadPool.globalInstance()
            self.threadpool.setMaxThreadCount(NUM_THREADS)

        self.terminate = False

        # Timed enqueue for running
        self.timer = QTimer()
        self.timer.setInterval(TIMER_QUEUE)
        self.timer.timeout.connect(self.runQueue)

        msg = _('Initializing worker')
        if not NATIVE_THREADS:
            import threading
            self.threads = list()

        for w in range(1,NUM_THREADS+1):
            msg += " {}".format(w)
            worker = Worker(self.dispatched,self.lock,w)
            worker.newResult.connect(self.newResultCompleted)
            self.workers.append(worker)

            if NATIVE_THREADS:
                worker.setAutoDelete(True)
                #self.threadpool.start(worker)
            else:
                t = threading.Thread(target=worker.run,name="Thread {}".format(w))
                self.threads.append(t)
                #t.start()
        if self.debug_level > 0:
            qDebug(msg)
    
    def start_threads(self):
        num = 0
        self.timer.start()
        if NATIVE_THREADS:
            for w in self.workers:
                self.threadpool.start(w)
                num += 1
        else:
            for t in self.threads:
                t.start()
                num += 1
        if self.debug_level > 0:
            qDebug("{} {} {}".format(_('Started'),num,_('threads + timer')))

    def row_is(self,state,row,col):
        return True if state[2*row+col] == '1' else False
    def row_is_linked(self,state,row):
        return self.row_is(state,row,1)
    def row_is_fixed(self,state,row):
        return self.row_is(state,row,0)
    def first_of_linked_group(self,state,row):
        if not self.row_is_linked(state,row):
            return None
        r=row
        for i in range(2*r+1,-1,-2):
            if state[i] == '1':
                row-=1
                continue
            else:
                row+=1
                break
        if row > -1:
            return row
        else:
            return None

    # Timed enqueue for running jobs
    @Slot()
    def runQueue(self):
        if self.jobs:
            if self.debug_level > 0:
                njobs = self.jobs.qsize()
                if njobs:
                    qDebug('{} {} {}'.format(_('Running'),njobs,_('jobs')))
            while not self.jobs.empty():
                self.dispatched.put(self.jobs.get())

    # Signal for process new result
    @Slot(int,int,str)
    def newResultCompleted(self,row,dir,result):
        if self.debug_level > 1:
            qDebug("{} \'{}\' \'{}\' \'{}\'".format(_('(Update pool) New Result'),row,dir,result))
        if row not in self.model:
            self.lock.lock()
            self.model.setdefault(row,[False,False,False,False,None,None])
            self.lock.unlock()
        
        # Copy current status
        state = self.model[row][0:2]
        valid = self.model[row][2:4]
        res = self.model[row][4:6]
        
        # Mark as enabled or disabled view results
        if result:
            state[dir]=True
        else:
            state[dir]=False
        # Copy result
        res[dir]=result
        # Mark as updated
        valid[dir]=True
        # Build list
        l = state + valid + res
        # Update model
        self.lock.lock()
        self.model[row] = l
        self.lock.unlock()

        if self.debug_level > 2:
            for y in self.model:
                s =''
                for x in self.model[y]:
                    s+=' \'{}\''.format(x)
                qDebug(s)

        # Send signal for update graphics
        self.parent.newResultCompleted(row,dir,result)

    def abort(self):
        global NATIVE_THREADS

        if self.debug_level > 0:
            qDebug(_("Aborting UpdatePool"))
        self.jobs = None
        self.dispatched = None
        for x in self.workers:
            x.abort()
        self.timer.stop()
        if NATIVE_THREADS:
            self.threadpool.clear()
        
    def set_stateString(self,stateString):
        if stateString != self.stateString:
            self.stateString = stateString
            self.levels = int(len(stateString)/2)
            self.invalidate_model()

    def resetWorkers(self):
        if self.debug_level > 1:
            qDebug(_("Resetting workers"))
        for w in self.workers:
            w.killresolver()

    def invalidate_model(self):
        if self.debug_level > 1:
            qDebug(_("Invalidating pool model"))
        self.resetWorkers()
        # Remove current job queue
        while not self.jobs.empty():
            self.jobs.get()

        self.lock.lock()
        # Initially create new model 
        if not self.model:
            self.model = {}
            self.model[0] =[False,True,True,False,None,None]
            for x in range(1,self.levels-1):
                self.model[x]=[True,True,False,False,None,None]
            self.model[self.levels] =[True,False,False,True,None,None]
        else:
            # Invalidate all model
            for x in self.model:
                self.model[x][2]=False
                self.model[x][3]=False
        self.lock.unlock()

        # Enqueue jobs for running
        done=[]
        for row in range(self.levels):
            r = row
            if r in done:
                continue
            if self.row_is_linked(self.stateString,r):
                first = self.first_of_linked_group(self.stateString,r)
                if first is not None:
                    done.append(first)
                    r = first        
            if r==0:
                self.jobs.put((self.stateString,row,Direction.DOWN.value))
            elif r==self.levels:
                self.jobs.put((self.stateString,row,Direction.UP.value))
            else:
                self.jobs.put((self.stateString,row,Direction.UP.value))
                self.jobs.put((self.stateString,row,Direction.DOWN.value))

    # Get status for enable/disable movement buttons, called from table delegate class
    def get_model_dirstate(self,state,row,direction):
        if state != self.stateString:
            self.set_stateString(state)
        if self.row_is_linked(self.stateString,row):
            first = self.first_of_linked_group(self.stateString,row)
            if first:
                row = first
        if row in self.model:
            state = self.model[row][direction]
            valid = self.model[row][self.modelStateOffset+direction]
        else:
            state = False
            valid = False
        if not valid:
            self.jobs.put((self.stateString,row,direction))
        return state

    # Get movement for clicked move cell
    def get_model_moveresult(self,state,row,direction):
        if state != self.stateString:
            self.set_stateString(state)
        if self.row_is_linked(self.stateString,row):
            first = self.first_of_linked_group(self.stateString,row)
            if first:
                row = first
        if row in self.model:
            state = self.model[row][self.modelStateOffset+direction]
            result = self.model[row][self.modelResultOffset+direction]
        else:
            state = False
        if not state:
            self.jobs.put((self.stateString,row,direction))
            return None
        return [result]
