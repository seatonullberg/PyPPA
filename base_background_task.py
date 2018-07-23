import pickle
import os
import threading
from threading import Thread
import time
import sys
import datetime


class BaseBackgroundTask(Thread):

    def __init__(self, delays, name):
        # this gets passed in and defines the delay between task iterations
        # [(func, seconds),...]
        self.delays = delays
        super().__init__()
        # name same format as plugin ex) reddit_tasks.py -> reddit_tasks
        # use underscore to differentiate from the thread's name attribute
        self._name = name
        self.daemon = True

    @property
    def config_obj(self):
        '''
        Load the configuration data into a convenient dict
        :return: dict(config_dict)
        '''
        try:
            # load the configuration pickle
            config_pickle_path = [os.getcwd(), 'public_pickles', 'configuration.p']
            config_pickle_path = os.path.join('', *config_pickle_path)
            config_obj = pickle.load(open(config_pickle_path, 'rb'))
        except FileNotFoundError:
            print("Unable to load a configuration")
            raise

        return config_obj

    @property
    def frame_data(self):
        '''
        Load the pickled dictionary of visual information produced by Watcher
        :return: dict(frame_data)
        '''
        frame_data_path = [os.getcwd(), 'public_pickles', 'frame_data.p']
        try:
            frame_data = pickle.load(open(os.path.join('', *frame_data_path), 'rb'))
        except EOFError:
            print('pickle EOF error')
        except pickle.UnpicklingError:
            print('pickle unpickling error')
        except FileNotFoundError:
            print('The frame_data.p file has not been generated or is not located at: {}'.format(
                os.path.join('', *frame_data_path)
                )
            )
            raise
        else:
            return frame_data

    def log(self, msg):
        '''
        Write a message to log file with some metadata
        :param msg: str() information to record in log file as a string
        :return: None
        '''
        assert type(msg) == str
        caller_name = sys._getframe(2).f_code.co_name
        caller_name = "Task: {}".format(caller_name)
        timestamp = datetime.datetime.utcnow()
        timestamp = "Time (UTC): {}".format(timestamp)
        log_message = "\n{}\n{}\n{}\n".format(caller_name,
                                              timestamp,
                                              msg)
        folder_name = ''.join([s.capitalize() for s in self.name.split('_')])
        log_file_path = [os.getcwd(), 'Plugins', folder_name, '{}.log'.format(folder_name)]
        log_file_path = os.path.join('', *log_file_path)
        with open(log_file_path, 'a') as log_file:
            log_file.write(log_message)

    def run(self):
        '''
        Override the Thread run method to monitor all the tasks in the class
        :return: None
        '''
        last_completion = {f: 0 for f, d in self.delays}
        for f, d in self.delays:
            # this means the functions cannot take any args
            # not ideal but also not a huge issue
            Thread(target=f, name=f.__name__).start()
        # iterate over all the tasks checking if they have exceeded their delay
        # if the delay is exceeded, start the task and reset the counter
        while True:
            active_thread_names = [t.name for t in threading.enumerate()]
            for f, d in self.delays:
                if f.__name__ not in active_thread_names:
                    last_completion[f] += 1
                    if last_completion[f] > d:
                        Thread(target=f, name=f.__name__).start()
                        last_completion[f] = 0
            # sleep for one second so each count is spread by approximately 1 second
            # therefore the delay passed in should be in units of seconds
            time.sleep(1)

    def vocalize(self, text):
        '''
        Synthesize and play speech from text
        :param text: the content to synthesize
        :return: None
        '''
        vocalize_path = [os.getcwd(), 'tmp', 'vocalize.txt']
        vocalize_path = os.path.join('', *vocalize_path)
        with open(vocalize_path, 'w') as f:
            f.write(text)
        while os.path.isfile(vocalize_path):
            continue


