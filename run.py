#!/usr/bin/python
from floating_listener import FloatingListener
from Listener import BackgroundListener
from Watcher import BackgroundWatcher
from multiprocessing import Process
import pickle
import os
from private_config import DATA_DIR


if __name__ == "__main__":
    # pickle the initial state of the floating listener
    fl = FloatingListener()
    fl_path = [DATA_DIR, 'public_pickles', 'listener.p']
    pickle.dump(fl, open(os.path.join('', *fl_path)), 'wb')
    # initialize the listener and watcher and await vocal command or visual cue
    watch = BackgroundWatcher()
    Process(target=watch.startup, name='Watcher').start()
    # allow listener to be the main process to save processes for background tasks
    listen = BackgroundListener()
    listen.startup()
