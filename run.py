#!/usr/bin/python
import os
import atexit
from multiprocessing import Process
from ctypes import *
from Services.ListenerService.listener_service import ListenerService
from Services.SpeakerService.speaker_service import SpeakerService
from Services.WatcherService.watcher_service import WatcherService
from generate_config import Configuration
from Plugins.SleepPlugin.sleep_plugin import SleepPlugin


@atexit.register
def cleanup():
    # delete all files in the tmp dir
    tmp_path = [os.getcwd(), 'tmp']
    tmp_path = os.path.join('', *tmp_path)
    for fname in os.listdir(tmp_path):
        fpath = os.path.join(tmp_path, fname)
        os.remove(fpath)


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
    o = ListenerService()
    Process(target=o.mainloop, name='Listener').start()

    # initialize speaker in child process
    o = SpeakerService()
    Process(target=o.mainloop, name='Speaker').start()

    # initialize watcher in a child process
    o = WatcherService()
    Process(target=o.mainloop, name='Watcher').start()

    # initialize sleep plugin in child process
    o = SleepPlugin()
    cmd = 'sleep'
    Process(target=o.initialize, name=o.name, args=(cmd,)).start()
