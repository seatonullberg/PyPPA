#!/usr/bin/python
from multiprocessing import Process
from ctypes import *
from Listener import Listener
from Speaker import Speaker
from Watcher import BackgroundWatcher
from generate_config import Configuration
from Plugins.SleepPlugin.sleep_plugin import SleepPlugin
from BackgroundTasks.VisualTasks.visual_tasks import VisualTasks



def alsa_error_handler(a,b,c,d,e):
    pass


if __name__ == "__main__":
    # ignore the alsa warnings
    ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
    c_error_handler = ERROR_HANDLER_FUNC(alsa_error_handler)
    asound = cdll.LoadLibrary('libasound.so')
    # Set error handler
    asound.snd_lib_error_set_handler(c_error_handler)

    # make config first
    o = Configuration()
    o.make()

    # initialize listener in child process
    o = Listener()
    Process(target=o.mainloop, name='Listener').start()

    # initialize speaker in child process
    o = Speaker()
    Process(target=o.mainloop, name='Speaker').start()

    # initialize the watcher in a child process
    o = BackgroundWatcher()
    Process(target=o.startup, name='Watcher').start()

    # initialize visual tasks in a child process
    o = VisualTasks()
    Process(target=o.run, name=o.name).start()

    # initialize sleep plugin in child process
    o = SleepPlugin()
    Process(target=o.initialize, name=o.name).start()
