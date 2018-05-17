#!/usr/bin/python
from Listener import BackgroundListener
from Watcher import BackgroundWatcher
from config import BACKGROUND_TASKS
from threading import Thread

if __name__ == "__main__":
    # spawn a thread for each background task to spin in
    for task in BACKGROUND_TASKS:
        task = task()
        Thread(target=task.startup).start()

    # initialize the listener and watcher and await vocal command or visual cue
    listen = BackgroundListener()
    Thread(target=listen.startup).start()
    watch = BackgroundWatcher()
    Thread(target=watch.startup).start()
