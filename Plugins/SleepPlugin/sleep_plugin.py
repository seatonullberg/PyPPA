import multiprocessing
from base_plugin import BasePlugin


class SleepPlugin(BasePlugin):

    def __init__(self):
        self.name = 'SleepPlugin'
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

        # initialize the flask app
        args_dict = {'name': self.name,
                     'html': 'Awake...'}
        self.serve_flask_app(args_dict)
        driver = self.generate_webdriver()
        driver.get(self.flask_url)

        # ask for and collect command
        print("Awake...")
        self.vocalize("how can I help you?")
        cmd = self.get_command()
        print(cmd)

        # iterate over all plugins to try and find one that supports a command hook found in cmd
        # do not iterate over the betas -- they must be handled by their own plugin
        # TODO: move this functionality to a utils file because other plugins will need similar behavior
        for plugin_name in self.config_obj.plugins:
            chd = self.config_obj.plugins[plugin_name]['command_hook_dict']
            for hook in chd:
                for variant in chd[hook]:
                    # if there is a match in the command and command hook dict, establish that plugin as the
                    # active context and prepare for command execution
                    if variant in cmd:
                        # check to see if the plugin is already running in background
                        active_proc_names = [p.name for p in multiprocessing.active_children()]
                        if plugin_name in active_proc_names:
                            # send message
                            self.pass_and_remain(name=plugin_name, cmd=cmd)
                        else:
                            # initialize without message because plugin is not yet listening
                            self.initialize_and_remain(name=plugin_name, cmd=cmd)
                        return

    def sleep(self):
        print('Sleeping...')
        self.reset_threshold()
