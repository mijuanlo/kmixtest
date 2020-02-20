#
# START EDITABLE VARS
#

RESOURCES_PATH = [ ".", "./lib", "/usr/lib/kmixtest" ]

# IM_DEBUGGING: Fill editable vars with optimal values
IM_DEBUGGING = False

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
    'option': 'option.svg',
    'add': 'add.png',
    'exit': 'exit.png',
    'new': 'new.png',
    'nok': 'nok.png',
    'ok': 'ok.png',
    'print': 'print.png',
    'remove': 'remove.png',
    'save': 'save.png',
    'okbw': 'okbw.png',
    'lock': 'lock.png',
    'unlock': 'unlock.png',
    'alertbw': 'alertbw.svg',
    'negated': 'nok.svg',
    'image': 'image.png',
    'image_missing': 'image-missing.png',
    'remove_image': 'remove-image.png',
    'high': 'high.png',
    'low': 'low.png'
    }

ARTWORK = {
    'left':'college.png',
    'center':'department.jpg'
    }

UI = "mainwindow.ui"

from os import cpu_count
import sys

if IM_DEBUGGING:
    NUM_THREADS = 1
    DEBUG_LEVEL = 2
    NATIVE_THREADS = False
    TIMER_QUEUE=1000
else:
    NUM_THREADS = cpu_count()

if not NATIVE_THREADS:
    import threading

import os

ICONPATH = ""
UIPATH = ""
ARTWORKPPATH = ""

rdir = ""
for resourcedir in RESOURCES_PATH:
    resourcedir = os.path.abspath(resourcedir)
    if os.path.isdir(resourcedir):
        uidir = resourcedir + '/'
        icondir = resourcedir + '/icons'
        artworkdir = resourcedir + '/artwork'

        uifile = uidir + '/' + UI
        if not os.path.isfile(uifile):
            if DEBUG_LEVEL > 1:
                print("{} not found!".format(uifile))
        else:
            UI = uifile
            UIPATH = uidir

        if os.path.isdir(icondir):
            for x in ICONS:
                icon = icondir + '/' + ICONS[x]
                if not os.path.isfile(icon):
                    if DEBUG_LEVEL > 1:
                        print("{} not found!".format(icon))
                else:
                    ICONS[x] = icon
            ICONPATH = icondir

        if os.path.isdir(artworkdir):
            for x in ARTWORK:
                artfile = artworkdir + '/' + ARTWORK[x]
                if not os.path.isfile(artfile):
                    if DEBUG_LEVEL > 1:
                        print("{} not found!".format(artfile))
                else:
                    ARTWORK[x] = artfile
            ARTWORKPPATH = artworkdir
        if ARTWORKPPATH and ICONPATH and UIPATH:
            rdir = resourcedir

if rdir:
    RESOURCES_PATH = rdir
else:
    sys.exit(1)


