import webbrowser
from Speaker import vocalize
from floating_listener import listen_and_convert
from mannerisms import Mannerisms

'''
TODO:
- use selenium sessions for improved interactivity
- add 'and' modifier
- ask for further commands to determine sleep/active status
'''


class PyPPA_WebBrowserPlugin(object):

    def __init__(self, command):
        self.command = command
        # remember to place the single word spelling last to avoid 'best spelling' issue
        self.COMMAND_HOOK_DICT = {'open': ['open up', 'open it', 'open'],
                                  'search': ['search for', 'search']}
        # use these functions to clarify what might be spelled incorrectly
        self.FUNCTION_KEY_DICT = {'canvas': ['canvas', 'e learning']}

    def function_handler(self, command_hook, spelling):
        '''
        Function required to map user commands with their final function
        :return: None
        '''
        if command_hook == 'search':
            # prepare for a google search
            search_query = self.command.replace(spelling, '')
            split_query = list(search_query.split(' '))
            search_query = '+'.join(split_query)
            self.google_search(search_query)
        else:
            # the open hook is being used

            # check for UFL canvas
            for variations in self.FUNCTION_KEY_DICT['canvas']:
                if variations in self.command:
                    self.open_canvas()
                    return
            # attempt to find correct website
            # improve with more robust command screening
            self.catch_all(spelling)

    def update_database(self):
        pass

    '''
    --------------------------------------------------------------------------------------------------------
    Begin Module Functions
    --------------------------------------------------------------------------------------------------------
    '''

    def catch_all(self, spelling):
        self.command = self.command.replace(spelling, '')
        command_no_spaces = self.command.replace(' ', '')
        webbrowser.open_new(r'http://www.'+command_no_spaces+'.com/')

    def open_canvas(self):
        webbrowser.open_new(r'https://ufl.instructure.com/')

    def google_search(self, search_query):
        webbrowser.open_new('https://www.google.com/search?q='+search_query)
