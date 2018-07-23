from base_beta import BaseBeta


class NetflixSearchBeta(BaseBeta):

    def __init__(self):
        self.COMMAND_HOOK_DICT = {'search': ['search for ', 'search'],
                                  'play': ['play']}
        self.MODIFIERS = {'search': {},
                          'play': {}}
        super().__init__(command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS,
                         name='netflix_search_beta')
        self.status = None

    def search(self):
        driver = self.DATA
        driver.get('https://www.netflix.com/search?q={}'.format(self.command_dict['premodifier']))
        self.status = 'search'

    def play(self):
        raise NotImplementedError()

