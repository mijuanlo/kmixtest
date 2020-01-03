#
# START EDITABLE VARS
#

# IM_DEBUGGING: Fill editable vars with optimal values
IM_DEBUGGING = 1 # False

# Thread limit
NUM_THREADS = 1

# Debug level for internal resolver & movement, printing terminal messages
#  values: 0 (disabled), 1 (less verbose), 2 (full debug messages)
DEBUG_LEVEL = 0

# Use Qt's thread workers
NATIVE_THREADS = True

# Job update interval
TIMER_QUEUE=500

#
# END EDITABLE VARS
#

ICONS = {
    'up':'go-up.svg',
    'down':'go-down.svg',
    'linked':'linked.svg',
    'fixed': 'fixed.svg',
    'close': 'close.svg',
    'option': 'option.svg'
    }

from os import cpu_count

if IM_DEBUGGING:
    NUM_THREADS = 1
    DEBUG_LEVEL = 2
    NATIVE_THREADS = False
    TIMER_QUEUE=1000
else:
    NUM_THREADS = cpu_count()

if not NATIVE_THREADS:
    import threading