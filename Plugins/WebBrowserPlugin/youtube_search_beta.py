from base_beta import BaseBeta


class YoutubeSearchBeta(BaseBeta):

    def __init__(self):
        self.COMMAND_HOOK_DICT = {'search': ['search for', 'search']}
        self.MODIFIERS = {'search': {}}
        super().__init__(command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS,
                         name='youtube_search_beta',
                         alpha_name='WebBrowserPlugin')

    def search(self):
        driver = self.DATA
        driver.get('https://www.youtube.com/results?search_query={}'.format(self.command_dict['premodifier']))

    def exit_context(self, cmd=None):
        self.DATA.quit()
        super().exit_context(cmd)