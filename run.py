#!/usr/bin/python
import Listener
from config import BACKGROUND_TASKS
from threading import Thread
'''
use this file to organize initialization such as threading across multiple sensory inputs
--when others are added
'''


if __name__ == "__main__":
    # spawn a thread for each background task to spin in
    for task in BACKGROUND_TASKS:
        task = task()
        Thread(target=task.startup).start()
    # initialize the listener and await vocal command
    listen = Listener.InitializeBackgroundListening()
    listen.startup()
