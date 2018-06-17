from Plugins.base_plugin2 import BasePlugin


class PyPPA_SleepPlugin(BasePlugin):

    def __init__(self, command):
        self.name = 'SleepPlugin'
        self.COMMAND_HOOK_DICT = {'wake_up': ['hey auto', 'wake up']}
        self.MODIFIERS = {'wake_up': {}}
        super().__init__(command=command,
                         command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS)

    def function_handler(self, args=None, self_obj=None):
        super().function_handler(self_obj=self)
        if self.isActive:
            self.reset_command_dict()
            self.listener().listen_and_execute(context=self)
        else:
            while not self.isActive:
                continue
            self.function_handler()

    def wake_up(self):
        print('waking up')
        # leave empty context to determine one
        # self.listener().listen_and_execute()
