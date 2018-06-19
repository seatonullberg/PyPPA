import os
import multiprocessing
from multiprocessing import Process
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
        print("Woken up, speak now")
        cmd = self.listener.listen_and_convert()
        print(cmd)
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
                            # activate and initialize
                            # this is cut and paste I should move somewhere
                            plugin_class_name = plugin_name.split('_')
                            plugin_class_name = [p.capitalize() for p in plugin_class_name]
                            plugin_class_name = ''.join(plugin_class_name)
                            # import the plugin class to obj_plugin
                            mod_str = "Plugins.{cn}.{n}".format(cn=plugin_class_name,
                                                                n=plugin_name)
                            module = __import__(mod_str, fromlist=[plugin_class_name])
                            # remove self from active status
                            self.isActive = False
                            # activate and start in a child process
                            plugin_obj = getattr(module, plugin_class_name)()
                            Process(target=plugin_obj.initialize, args=(cmd,), name=plugin_obj.name).start()
                        return

    def sleep(self):
        print('sleeping')

