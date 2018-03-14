import wikipedia
import requests
from Speaker import vocalize
from floating_listener import listen_and_convert
from bs4 import BeautifulSoup


class PyPPA_TeacherPlugin(object):

    def __init__(self, command):

        self.command = command
        self.COMMAND_HOOK_DICT = {'teach me': ['teach me about', 'teach me']}

        self.FUNCTION_KEY_DICT = {'how to': ['how too', 'hot to', 'hot too', 'how to']}

    def function_handler(self, command_hook, spelling):
        # seems unnecessary but leaves room for growth
        for variations in self.FUNCTION_KEY_DICT['how to']:
            if variations in self.command:
                self.scrape_wikihow(spelling, variations)
                return

        self.basic_teach(spelling)

    def update_database(self):
        pass

    '''
    --------------------------------------------------------------------------------------------------------
    Begin Module Functions
    --------------------------------------------------------------------------------------------------------
    '''

    def basic_teach(self, hook_spelling):
        try:
            query = self.command.replace(hook_spelling, '')
            summary = wikipedia.summary(query, auto_suggest=True)
            vocalize('ok, this is what i know about '+query)
            vocalize(summary)
        except wikipedia.DisambiguationError:
            vocalize('could you be more specific?')

    def scrape_wikihow(self, hook_spelling, function_spelling):
        query = self.command.replace(hook_spelling, '')
        query = query.replace(function_spelling, '')
        r = requests.get(r'https://www.wikihow.com/'+query)

        readable = r.text
        soup = BeautifulSoup(readable, 'html.parser')

        reading_text = []
        for paragraphs in soup.find_all('div', {'class': 'step'}):
            p_text = paragraphs.text
            for scripts in paragraphs.find_all('script'):
                s_text = scripts.text
                p_text = p_text.replace(s_text, '')
            reading_text.append(p_text)

        if len(reading_text) < 1:
            vocalize('sorry, i do not know how to ' + query)
        else:
            reading_text = ' '.join(reading_text)
            print(reading_text)
            vocalize('ok, this is how to ' + query)
            vocalize(reading_text)