import wikipedia
import requests
from Speaker import vocalize
from bs4 import BeautifulSoup
from Plugins.base_plugin import BasePlugin


class PyPPA_TeacherPlugin(BasePlugin):

    def __init__(self, command):
        self.COMMAND_HOOK_DICT = {'teach_me': ['teach me about', 'teach me']}
        self.MODIFIERS = {'teach_me': {'how_to': ['how too', 'hot to', 'hot too', 'how to']}}
        super().__init__(command=command,
                         command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS)

    def function_handler(self, args=None):
        # this is not robust for future intraplugin changes
        if self.command_dict['modifier'] != '':
            self.scrape_wikihow(self.command_dict['postmodifier'])
            return

        self.basic_teach(self.command_dict['premodifier'])

    def update_database(self):
        pass

    '''
    --------------------------------------------------------------------------------------------------------
    Begin Module Functions
    --------------------------------------------------------------------------------------------------------
    '''

    def basic_teach(self, query):
        try:
            summary = wikipedia.summary(query, auto_suggest=True)
            vocalize('ok, this is what i know about '+query)
            vocalize(summary)
        except wikipedia.DisambiguationError:
            vocalize('could you be more specific?')

        self.isBlocking = False

    def scrape_wikihow(self, query):
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

        self.isBlocking = False
