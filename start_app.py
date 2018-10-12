#!/usr/bin/python
import os
import atexit
from ctypes import *

from app import App


@atexit.register
def cleanup():
    # delete all files in the tmp dir
    tmp_path = [os.getcwd(), 'tmp']
    tmp_path = os.path.join('', *tmp_path)
    for fname in os.listdir(tmp_path):
        if fname != 'README.md':
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

    app = App()
    app.start()
