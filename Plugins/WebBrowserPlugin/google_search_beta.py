from base_beta import BaseBeta


class GoogleSearchBeta(BaseBeta):

    def __init__(self):
        self.COMMAND_HOOK_DICT = {'search': ['search for ', 'search']}
        self.MODIFIERS = {'search': {}}
        super().__init__(command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS,
                         name='google_search_beta')
        # more convenient variable name

    def search(self):
        driver = self.DATA
        print('google_search_beta initialized')
        driver.get('https://www.google.com/search?q={}'.format(self.command_dict['premodifier']))
