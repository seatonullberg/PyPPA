import time
from Speaker import vocalize
from config import PLUGIN_LIST
from mannerisms import Mannerisms
from floating_listener import listen_and_convert


def update_plugins():
    for plugin in PLUGIN_LIST:
        p = plugin('')
        p.update_database()
    print('Updates Complete')


class InitializeBackgroundListening(object):

    def __init__(self):
        self.triggers = ['hey Auto', 'hey auto', 'wake up', 'Auto', 'auto']
        update_plugins()

    def startup(self):
        '''
        listens for trigger
        :return: None, calls collect_command to collect next incoming audio
        '''
        while True:
            recorded_input = listen_and_convert(pre_buffer=None)
            for trigger in self.triggers:
                try:
                    if trigger in recorded_input:
                        vocalize(Mannerisms('await_command', None).final_response)
                        self.collect_and_process()
                except TypeError:
                    # when the recorded input is None
                    continue

    def collect_and_process(self):
        recorded_input = listen_and_convert(pre_buffer=10)
        try:
            recorded_input = recorded_input.lower()
            print('collect_and_process heard: {}'.format(recorded_input))
        except TypeError:
            # when recorded is None
            print('No command was recorded. Going to sleep')
            return

        for plugin in PLUGIN_LIST:
            # check all installed modules
            plugin = plugin(recorded_input)
            for command_hook in plugin.COMMAND_HOOK_DICT:
                for spelling in plugin.COMMAND_HOOK_DICT[command_hook]:
                    if spelling in recorded_input:
                        # carry out request and go back to listening
                        plugin.function_handler(command_hook, spelling)
                        while plugin.isBlocking:
                            time.sleep(0.5)
                        return
        # if all fail
        vocalize(Mannerisms('unknown_command', {'command': recorded_input}).final_response)
