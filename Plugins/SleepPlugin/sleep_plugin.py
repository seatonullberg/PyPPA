from Plugins import base


class SleepPlugin(base.Plugin):

    def __init__(self):
        """
        Acts as the default behavior when all other plugins are inactive
        - scans for commands and assigns them to other plugins
        """
        self.name = 'SleepPlugin'
        self.command_hooks = {self.wake_up: ['hey auto', 'wake up'],
                              self.sleep: ['go to sleep', 'sleep']}
        self.modifiers = {self.wake_up: {},
                          self.sleep: {}}
        super().__init__(name=self.name,
                         command_hooks=self.command_hooks,
                         modifiers=self.modifiers)

    def wake_up(self):
        '''
        Listen for a command and send it to the proper plugin
        :return: None
        '''
        # ask for and collect command
        print("Awake...")
        self.vocalize("how can I help you?")
        cmd = self.get_command()
        print(cmd.input_string)

        self.request_plugin(command_string=cmd.input_string)  # request the first plugin to accept the command

    def sleep(self):
        """
        Dummy method to retain inactive state
        """
        print('Sleeping...')
        self.reset_threshold()
