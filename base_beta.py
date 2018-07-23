from base_plugin import BasePlugin


class BaseBeta(BasePlugin):

    def __init__(self, command_hook_dict, modifiers, name, alpha_name):
        # store the alpha plugin's name
        self.alpha_name = alpha_name
        # the data passed by the alpha plugin
        self.DATA = None
        super().__init__(command_hook_dict=command_hook_dict,
                         modifiers=modifiers,
                         name=name)
        # add exit context as a command for all
        self.COMMAND_HOOK_DICT['exit_context'] = ['exit context']
        self.MODIFIERS['exit_context'] = {}

    def initialize(self, cmd=None, data=None):
        self.DATA = data
        self.make_active()
        self.mainloop(cmd)

    def exit_context(self, cmd=None):
        self.pass_and_terminate(name=self.alpha_name,
                                cmd=cmd)
