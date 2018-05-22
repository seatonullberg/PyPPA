import random


# TODO: add more contexts
class Mannerisms(object):

    def __init__(self, context, response_fill_dict):
        self.context = context
        self.final_response = None
        self.response_fill_dict = response_fill_dict
        self.CONTEXT_DICT = {'unknown_command': self.unknown_command_handler,
                             'await_command': self.await_command_handler,
                             'request_subsequent_command': self.request_subsequent_command_handler,
                             'error': self.error_handler,
                             'unknown_audio': self.unknown_audio_handler}
        self.context_manager()

    def context_manager(self):
        for context_key in self.CONTEXT_DICT:
            if self.context == context_key:
                self.CONTEXT_DICT[context_key]()
                return

        print('this context is not defined')

    def unknown_command_handler(self):
        # this context is used when an unknown command is supplied
        # requires a response fill string
        responses = ['Sorry, I am not sure how to '+self.response_fill_dict['command'],
                     'Sorry, I have never been taught how to '+self.response_fill_dict['command'],
                     'Unfortunately, '+self.response_fill_dict['command']+' is not in my skill set']
        seed = random.randint(0, len(responses)-1)
        self.final_response = responses[seed]

    def await_command_handler(self):
        # this context is used when the program asks if you need anything and then listens
        # no fill string
        responses = ['How can I help you?', 'What would you like me to do?']
        seed = random.randint(0, len(responses)-1)
        self.final_response = responses[seed]

    def request_subsequent_command_handler(self):
        # this context is used when a command has already been executed and PyPPA is ready for another
        # no fill string
        responses = ['Will that be all?', 'Do you need anything else?', 'Any other requests?']
        seed = random.randint(0, len(responses)-1)
        self.final_response = responses[seed]

    def error_handler(self):
        # this context is used for generalized errors that require or provide no explanation
        # no fill string
        responses = ['Sorry, something went wrong.',
                     'Sorry, an error occured.',
                     'I ran into an issue, please try again.']
        seed = random.randint(0, len(responses) - 1)
        self.final_response = responses[seed]

    def unknown_audio_handler(self):
        # this context is used when audio commands cannot be deciphered to a string
        # no fill string
        responses = ['I could not make sense of that, please repeat.',
                     'I was not able to understand that, could you try again?']
        seed = random.randint(0, len(responses) - 1)
        self.final_response = responses[seed]