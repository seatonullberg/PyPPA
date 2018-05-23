import time
from Speaker import vocalize
from config import PLUGIN_LIST
from mannerisms import Mannerisms
from floating_listener import FloatingListener


def update_plugins():
    for plugin in PLUGIN_LIST:
        p = plugin('')
        p.update_plugin()
    print('Updates Complete')


class BackgroundListener(FloatingListener):

    def __init__(self):
        super().__init__()
        self.triggers = ['hey Auto', 'hey auto', 'wake up', 'Auto', 'auto']
        update_plugins()

    def startup(self):
        '''
        listens for trigger
        :return: None, calls collect_command to collect next incoming audio
        '''
        while True:
            recorded_input = self.listen_and_convert()
            for trigger in self.triggers:
                try:
                    if trigger in recorded_input:
                        vocalize(Mannerisms('await_command', None).final_response)
                        self.collect_and_process()
                except TypeError:
                    # when the recorded input is None
                    continue

    def collect_and_process(self):
        print('collect and process starting')
        # set new prebuffer for recording
        recorded_input = self.listen_and_convert()
        try:
            recorded_input = recorded_input.lower()
            print('collect_and_process heard: {}'.format(recorded_input))
        except AttributeError:
            # when recorded is None
            print('No command was recorded. Going to sleep')
            return

        for plugin in PLUGIN_LIST:
            plugin = plugin(recorded_input)
            if plugin.acceptsCommand:
                plugin.function_handler()
                while plugin.isBlocking:
                    time.sleep(0.5)
                return
            else:
                continue

        # if all fail
        vocalize(Mannerisms('unknown_command', {'command': recorded_input}).final_response)
