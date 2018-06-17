import multiprocessing
from multiprocessing import Process
from Speaker import vocalize
from base_plugin import BasePlugin


class BackgroundTaskPlugin(BasePlugin):

    def __init__(self):
        self.name = 'background_task_plugin'
        self.COMMAND_HOOK_DICT = {'run': ['start running my', 'start running',
                                          'run my', 'start my', 'start', 'run'],
                                  'stop': ['stop running my', 'stop running',
                                           'stop my', 'quit my', 'kill my',
                                           'stop', 'quit', 'kill']
                                  }
        self.MODIFIERS = {'run': {'reddit_tasks': ['reddit tasks', 'reddit task', 'reddit'],
                                  'wikipedia_tasks': ['wikipedia tasks', 'wikipedia task', 'wikipedia'],
                                  'all': ['all tasks', 'all']
                                  }
                          }
        # run and stop have the same modifiers
        self.MODIFIERS['stop'] = self.MODIFIERS['run']
        super().__init__(command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS,
                         name=self.name)

    def function_handler(self, args=None):
        current_processes = multiprocessing.active_children()
        # default modifier is 'all'
        if self.command_dict['modifier'] == '':
            self.command_dict['modifier'] = 'all'

        if self.command_dict['command_hook'] == 'run':
            # start a new process
            from BackgroundTasks.Reddit.reddit_tasks import startup as reddit_startup
            from BackgroundTasks.Wikipedia.wikipedia_tasks import startup as wikipedia_startup
            if len(current_processes) >= multiprocessing.cpu_count()-1:
                vocalize('There are currently too many processes running to do that.')
            elif self.command_dict['modifier'] == 'reddit_tasks':
                Process(target=reddit_startup, name='reddit_tasks').start()
            elif self.command_dict['modifier'] == 'wikipedia_tasks':
                Process(target=wikipedia_startup, name='wikipedia_tasks').start()
            else:
                # run all
                # if there are more processes to run than available cores, don't run any
                if len(current_processes) >= (multiprocessing.cpu_count() -
                                              len(self.MODIFIERS[self.command_dict['command_hook']])):
                    vocalize('There are currently too many processes running to do that.')
                else:
                    Process(target=reddit_startup, name='reddit_tasks').start()
                    Process(target=wikipedia_startup, name='wikipedia_tasks').start()
        else:
            # terminate specified process
            if self.command_dict['modifier'] != 'all':
                for proc in current_processes:
                    if proc.name == self.command_dict['modifier']:
                        proc.terminate()
                        proc.join()
            else:
                # terminate any and all background processes
                for proc in current_processes:
                    if proc.name in self.MODIFIERS[self.command_dict['command_hook']]:
                        proc.terminate()
                        proc.join()
        self.isBlocking = False
