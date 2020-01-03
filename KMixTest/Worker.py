from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtPrintSupport import *
from PySide2.QtUiTools import *

from queue import Queue, Empty
from time import sleep, time

from .Config import DEBUG_LEVEL, NATIVE_THREADS
from .Util import mychr, unmychr, Direction, Color
from .ResolverCached import ResolverCached

class Worker (QRunnable,QObject):
    newResult = Signal(int,int,str)
    def __init__(self,joblist,mutex,id):
        global DEBUG_LEVEL, NATIVE_THREADS
        self.debug_level = DEBUG_LEVEL
        QObject.__init__(self)
        if NATIVE_THREADS:
            QRunnable.__init__(self)
        # Queue of available jobs to do
        self.joblist = joblist
        self.lock = mutex
        self.id = id
        self.resolver = ResolverCached()
        self.terminate = False
        self.terminated = False

    def abort(self):
        if self.debug_level > 0:
            qDebug("Aborting worker {}".format(self.id))
        self.terminate = True
        self.joblist = None
        self.resolver.abort()
    def killresolver(self):
        if self.debug_level > 0:
            qDebug("Killing on worker {} internal resolver".format(self.id))
        self.resolver.reset()

    def row_is(self,state,row,col):
        return True if state[2*row+col] == '1' else False
    def row_is_linked(self,state,row):
        return self.row_is(state,row,1)
    def row_is_fixed(self,state,row):
        return self.row_is(state,row,0)

    def run(self):
        while not self.terminate:
            try:
                # Try to get a job from queue
                timeout = 0.01
                if not self.joblist.empty():
                    state,row,direction = self.joblist.get(block=True,timeout=timeout)
                else:
                    sleep(timeout)
                    continue
            except Empty:
                continue

            ID = mychr(row)
            ROW_COUNT = int(len(state)/2)

            strstate=state
            if self.debug_level > 0:
                strstate=''
                for x in range(len(state)):
                    level = int(x / 2)
                    change = x % 2
                    if change:
                        strstate += '{}({}{}) '.format(mychr(level),state[x-1],state[x])
                qDebug('Running worker #{} state={} row={} dir={}'.format(self.id,strstate,row,direction))

            ret = False
            # First can't go up and Last can't go down
            if row == 0 and direction == Direction.UP:
                ret = True
            if not ret and row == ROW_COUNT -1 and direction == Direction.DOWN:
                ret = True
            # Fixed rows can't move
            if not ret and self.row_is_fixed(state,row):
                ret = True
            
            # Linked rows with any of them fixed , can't move
            if not ret and self.row_is_linked(state,row):
                idx = row -1
                # search upward fixed row on linked group
                while idx > 0 and self.row_is_linked(state,idx):
                    if self.row_is_fixed(state,idx):
                        ret = True
                        break
                    else:
                        idx -= 1
                # search downward fixed row on linked group
                idx = row +1
                while idx < ROW_COUNT and self.row_is_linked(state,idx):
                    if self.row_is_fixed(state,idx):
                        ret = True
                        break
                    else:
                        idx += 1
            if ret:
                self.newResult.emit(row,direction,'')
            else:
                self.resolver.configureResolver(state,row,direction)
                stime = time()
                if self.debug_level > 0:
                    qDebug('#{}({}) can move {}? (Thinking...)'.format(unmychr(ID),ID,'DOWN' if direction else 'UP'))
                R = self.resolver.getResults()
                dur = time()-stime
                duration = "{0:4.2f}".format(dur)
                flagdirection = True if R else False
                result = R[0] if R else []
                s = '#{}({}) can move {}? {} [ {} secs ]'.format(unmychr(ID),ID,'DOWN' if direction else 'UP','YES' if result else 'NO',duration)
                if dur > 2.0:
                    qDebug(Color.makecolor(s,Color.RED))
                else:
                    if self.debug_level > 0:
                        qDebug(Color.makecolor(s,Color.GREEN))
                if self.debug_level > 0:
                    qDebug('End worker {} [ {} sec ]--> Sending: \'{}\' \'{}\' \'{}\' '.format(self.id,duration,row,direction,R))
                self.newResult.emit(row,direction,result)
            if self.joblist:
               self.joblist.task_done()
        self.terminated = True
