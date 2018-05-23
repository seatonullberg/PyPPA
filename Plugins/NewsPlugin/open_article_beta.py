from Speaker import vocalize
import webbrowser
# TODO: rewrite with new inheritance scheme


'''
-add ability to select an article by keyword in headline
'''


class OpenArticleBeta(object):

    def __init__(self, command, article_list):
        self.command = command
        self.article_list = article_list
        self.COMMAND_HOOK_DICT = {'yes': ['yes please', 'yeah', 'yes'],
                                  'no': ['no thanks', 'no']}
        self.FUNCTION_KEY_DICT = {'1': ['number 1', 'number one', 'one', 'first'],
                                  '2': ['number 2', 'number two', 'two', 'to', 'too', 'second'],
                                  '3': ['number 3', 'number three', 'three', 'third'],
                                  '4': ['number 4', 'forth', 'number four', 'four', 'fourth'],
                                  '5': ['number 5', 'last', 'number five', 'five', 'fifth']}

    def function_handler(self):
        for variations in self.COMMAND_HOOK_DICT['yes']:
            if variations in self.command:
                vocalize('here is the full story')
                self.generate_response()
                return
        for variations in self.COMMAND_HOOK_DICT['no']:
            if variations in self.command:
                return
        # if someone just says 'number 1' without yes then it still opens
        vocalize('here is the full story')
        self.generate_response()

    def update_database(self):
        pass

    def generate_response(self):

        for indices in self.FUNCTION_KEY_DICT:
            for variations in self.FUNCTION_KEY_DICT[indices]:
                if variations in self.command:
                    webbrowser.open_new(self.article_list[int(indices)-1]['url'])
                    return
        # if user only says 'yes' just open the first
        webbrowser.open_new(self.article_list[0]['url'])
