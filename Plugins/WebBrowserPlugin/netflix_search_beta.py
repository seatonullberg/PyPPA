from Plugins.base_plugin import BasePlugin


class NetflixSearchBeta(BasePlugin):

    def __init__(self, command):
        self.driver = None
        self.COMMAND_HOOK_DICT = {'search_for': ['search for', 'look for', 'find'],
                                  'play': ['play', 'start'],
                                  'pause': ['pause'],
                                  'go_back': ['go back to the menu', 'go back to menu', 'go back'],
                                  'release_context': ['release context', 'escape context']
                                  }
        self.MODIFIERS = {'search_for': {},
                          'play': {'number': ['result number', 'number', 'result']},    # select by row order
                          'pause': {}
                          }
        super().__init__(command=command,
                         command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS)


