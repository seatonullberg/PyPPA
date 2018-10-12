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

        # iterate over all plugins to try and find one that supports a command hook found in cmd
        # do not iterate over the betas -- they must be handled by their own plugin
        for plugin_name in self.configuration.plugins:
            accepts = self.request_command_acceptance(plugin_name=plugin_name,
                                                      command_string=cmd.input_string)
            if accepts:
                self.request_plugin(plugin_name, cmd.input_string)

    def sleep(self):
        """
        Dummy method to retain inactive state
        """
        print('Sleeping...')
        self.reset_threshold()
