from base_plugin import BasePlugin
from Speaker import vocalize


class SleepPlugin(BasePlugin):

    def __init__(self):
        self.name = 'sleep_plugin'
        self.COMMAND_HOOK_DICT = {'wake_up': ['hey auto', 'wake up'],
                                  'sleep': ['go to sleep', 'sleep']}
        self.MODIFIERS = {'wake_up': {},
                          'sleep': {}}
        super().__init__(name=self.name,
                         command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS)

    def wake_up(self):
        '''
        Listen for a command and send it to the proper plugin
        :return: None
        '''
        self.pass_and_terminate(name='sleep_plugin', cmd='go to sleep')
        # vocalize("How can I help You?")
        # cmd = self.listener.listen_and_convert()

    def sleep(self):
        print('sleeping')


