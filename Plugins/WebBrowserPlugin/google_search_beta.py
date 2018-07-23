from base_beta import BaseBeta


class GoogleSearchBeta(BaseBeta):

    def __init__(self):
        self.COMMAND_HOOK_DICT = {'search': ['search for', 'search'],
                                  'exit_context': ['exit context']}
        self.MODIFIERS = {'search': {},
                          'exit_context': {}}
        super().__init__(command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS,
                         name='google_search_beta',
                         alpha_name='WebBrowserPlugin')

    def search(self):
        driver = self.DATA
        driver.get('https://www.google.com/search?q={}'.format(self.command_dict['premodifier']))

    def exit_context(self, cmd=None):
        self.DATA.quit()
        super().exit_context(cmd)
