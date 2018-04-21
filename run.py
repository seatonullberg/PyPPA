#!/usr/bin/python
from Listener import InitializeBackgroundListening
from config import BACKGROUND_TASKS
from threading import Thread
'''
use this file to organize initialization such as threading across multiple sensory inputs
--when others are added
'''

# spawn a thread for each background task to spin in
for task in BACKGROUND_TASKS:
    task = task()
    Thread(target=task.startup).start()

# initialize the listener and await vocal command
listen = InitializeBackgroundListening()
listen.startup()
