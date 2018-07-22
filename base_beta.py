from base_plugin import BasePlugin


class BaseBeta(BasePlugin):

    def __init__(self, command_hook_dict, modifiers, name):
        # the data passed by the alpha plugin
        self.DATA = None
        super().__init__(command_hook_dict=command_hook_dict,
                         modifiers=modifiers,
                         name=name)

    def initialize(self, cmd=None, data=None):
        self.DATA = data
        self.make_active()
        self.mainloop(cmd)
