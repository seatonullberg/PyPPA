#!/usr/bin/python
from Listener import BackgroundListener
from Watcher import BackgroundWatcher
from multiprocessing import Process

if __name__ == "__main__":
    # initialize the listener and watcher and await vocal command or visual cue
    watch = BackgroundWatcher()
    Process(target=watch.startup, name='Watcher').start()
    # allow listener to be the main process to save processes for background tasks
    listen = BackgroundListener()
    listen.startup()
