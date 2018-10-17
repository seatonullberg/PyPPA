from Plugins import base


class WebBrowserPlugin(base.Plugin):

    def __init__(self):
        self.name = 'WebBrowserPlugin'
        # remember to place the single word spelling last to avoid 'best spelling' issue
        self.command_hooks = {self.search_google: ['search google for', 'search google', 'search for', 'google'],
                              self.search_netflix: ['search netflix for', 'search netflix', 'open netflix', 'netflix'],
                              self.search_youtube: ['search youtube for', 'search youtube', 'open youtube', 'youtube']}
        self.modifiers = {self.search_google: {},
                          self.search_netflix: {},
                          self.search_youtube: {}}
        super().__init__(command_hooks=self.command_hooks,
                         modifiers=self.modifiers,
                         name=self.name)

    def search_google(self):
        # send to the beta
        cmd = 'search {}'.format(self.command.premodifier)
        self.request_plugin(plugin_name='WebBrowserPlugin.GoogleSearchBeta',
                            command_string=cmd)

    def search_netflix(self):
        # send to beta
        cmd = 'search {}'.format(self.command.premodifier)
        self.request_plugin(plugin_name='WebBrowserPlugin.NetflixSearchBeta', command_string=cmd)

    def search_youtube(self):
        # send to beta
        cmd = 'search {}'.format(self.command.premodifier)
        self.request_plugin(plugin_name='WebBrowserPlugin.YoutubeSearchBeta', command_string=cmd)
