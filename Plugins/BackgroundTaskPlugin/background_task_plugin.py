import multiprocessing
from multiprocessing import Process
from Speaker import vocalize


class PyPPA_BackgroundTaskPlugin(object):

    def __init__(self, command):
        self.command = command
        self.COMMAND_HOOK_DICT = {'run': ['start running my', 'start running',
                                          'run my', 'start my', 'start', 'run'],
                                  'stop': ['stop running my', 'stop running',
                                           'stop my', 'quit my', 'kill my',
                                           'stop', 'quit', 'kill']
                                  }
        self.FUNCTION_KEY_DICT = {'reddit_tasks': ['reddit tasks', 'reddit task',
                                                  'reddit'],
                                  'wikipedia_tasks': ['wikipedia tasks', 'wikipedia task',
                                                     'wikipedia'],
                                  'all': ['all tasks', 'all']
                                  }
        self.isBlocking = True

    def function_handler(self, command_hook, spelling):
        current_processes = multiprocessing.active_children()
        function_to_run = 'all'
        for func in self.FUNCTION_KEY_DICT:
            for variation in self.FUNCTION_KEY_DICT[func]:
                if variation in self.command:
                    function_to_run = func
        if command_hook == 'run':
            from BackgroundTasks.Reddit.reddit_tasks import startup as reddit_startup
            from BackgroundTasks.Wikipedia.wikipedia_tasks import startup as wikipedia_startup
            if len(current_processes) >= multiprocessing.cpu_count()-1:
                vocalize('There are currently too many processes running to do that.')
            elif function_to_run == 'reddit_tasks':
                Process(target=reddit_startup, name='reddit_tasks').start()
            elif function_to_run == 'wikipedia_tasks':
                Process(target=wikipedia_startup, name='wikipedia_tasks').start()
            else:
                # run all
                if len(current_processes) >= multiprocessing.cpu_count()-len(self.FUNCTION_KEY_DICT):
                    vocalize('There are currently too many processes running to do that.')
                else:
                    Process(target=reddit_startup, name='reddit_tasks').start()
                    Process(target=wikipedia_startup, name='wikipedia_tasks').start()
        else:
            # terminate specified process
            if function_to_run != 'all':
                for proc in current_processes:
                    if proc.name == function_to_run:
                        proc.terminate()
                        proc.join()
            else:
                # terminate any and all background processes
                for proc in current_processes:
                    if proc.name in self.FUNCTION_KEY_DICT:
                        proc.terminate()
                        proc.join()
        self.isBlocking = False

    def update_database(self):
        pass


